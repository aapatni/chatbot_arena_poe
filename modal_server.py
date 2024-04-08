import os
import asyncio
from typing import List, AsyncIterable
import fastapi_poe as fp
from modal import Image, Stub, asgi_app, Dict, Secret
from supabase import create_client, Client


database = Dict.from_name("my-dict", create_if_missing=True)
stub = Stub("chatbot-arena")
REQUIREMENTS = ["fastapi-poe==0.0.36", "openai", "python-dotenv", "supabase"]
image = Image.debian_slim().pip_install(*REQUIREMENTS)
supabase = None



def print_query(request: fp.QueryRequest):
    print("Conversation ID:", request.conversation_id)
    for message in request.query:
        print(f"\tMessage ID: {message.message_id}, Content: {message.content[:20]}")

class ChatbotArenaBot(fp.PoeBot):
    async def get_response(self, request: fp.QueryRequest) -> AsyncIterable[fp.PartialResponse]:

        questions = ""

        zwsp_count = request.query[len(request.query)-2].content.count('\u200B')
        print(f"Number of ZWSPs: {zwsp_count}")

        bot_a = "GPT-3.5-Turbo"
        bot_b = "Claude-3-Sonnet"

        try:

            # STATE MACHINE
            match zwsp_count:
                case 1:
                    print_query(request)
                    request.query = [fp.ProtocolMessage(role="system", content=f"Generate 3 insightful and yet difficult questions to test another chatbots intelligence on the provided user topic."), request.query[-1]]
                    async for msg in fp.stream_request(
                        request=request,
                        bot_name=bot_a,
                        api_key=request.access_key,
                    ):
                        questions += msg.text
                        yield msg

                    yield fp.PartialResponse(text="\n\n**Now we'll ask the competitors these questions!**\n")
                    save_query = request.query
                    request.query = []
                    questions = [q for q in questions.split('\n') if q.endswith('?')]
                    for question in questions:
                        if question.strip():
                            request.query.append(fp.ProtocolMessage(role="user", content=question + "Answer in 40 words or less."))

                            # Create async iterators for both requests
                            gpt_iterator = aiter(fp.stream_request(request=request, bot_name=bot_a, api_key=request.access_key))
                            claude_iterator = aiter(fp.stream_request(request=request, bot_name=bot_b, api_key=request.access_key))

                            # Initialize response variables
                            gpt_out = ""
                            claud_out = ""

                            # Fetch responses from both bots concurrently
                            while True:
                                gpt_response, claude_response = await asyncio.gather(
                                    anext(gpt_iterator, None),
                                    anext(claude_iterator, None)
                                )

                                if gpt_response is None and claude_response is None:
                                    break
                                if gpt_response is not None:
                                    gpt_out += gpt_response.text
                                if claude_response is not None:
                                    claud_out += claude_response.text
                            yield fp.PartialResponse(text=f"### Question: {question}\n")
                            yield fp.PartialResponse(text=f"**{bot_a} Response:**\n```\n" + gpt_out + "\n```\n")
                            yield fp.PartialResponse(text=f"**{bot_b} Response:**\n```\n" + claud_out + "\n```\n")
                            request.query.pop()
                        
                    request.query = save_query
                    yield fp.PartialResponse(text="\n\nWho do you think won?\u200B\u200B")
                    print_query(request)
                    supabase.table("poebot").insert({
                        "id": request.conversation_id,
                        "message_id": request.query[-1].message_id,
                        "bot_a": bot_a,
                        "bot_b": bot_b,
                        "q1": questions[0],
                        "q2": questions[1],
                        "q3": questions[2],
                        "topic": request.query[-1].content if request.query else "No topic provided"
                    }).execute()
                
                case 2:
                    save_query = request.query
                    new_query = [fp.ProtocolMessage(role="system", 
                                    content=f"Please evaluate the users' bot preference. Please output .5 for a tie, 0 for {bot_a}, or 1 for {bot_b}. Only output the numeric value."),
                                request.query[-1]]
                    request.query = new_query
                    gpt_out = ""

                    async for gpt_response in fp.stream_request(request=request, bot_name=bot_a, api_key=request.access_key):
                        gpt_out += gpt_response.text
                    
                    request.query = save_query
                    
                    print("In Response we found the winner is: ", gpt_out)
                    gpt_out_cleaned = gpt_out.strip()
                    if "0.5" in gpt_out_cleaned or "tie" in gpt_out_cleaned.lower():
                        winner = None
                    elif "1" in gpt_out_cleaned:
                        winner = True
                    elif "0" in gpt_out_cleaned:
                        winner = False
                    else:
                        winner = None

                    print_query(request)
                    supabase.table("poebot").update({
                        "winner": winner
                    }).eq("id", request.conversation_id).eq("message_id", request.query[-3].message_id).execute()
                    yield fp.PartialResponse(text=(
                        "🎉 **Thanks for participating! Your response has been recorded.** 🎉\n\n"
                        f"Check out: [Chatbot Arena](https://chatbot-arena-poe.vercel.app/) to see the live rankings!\n\n"
                        "Would you like to play again? \n\n*Please provide a new topic if you do.*\u200B"
                    ))
                case _:
                    raise Exception("Something went wrong!")
        except Exception as e:    
            print(e)
            yield fp.PartialResponse(text="Sorry, I didn't understand that. Please start over and provide me with your topic.\u200B")
        
    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(
            allow_attachments=False,
            introduction_message = (
                "# 🎉 Welcome to the Chatbot Arena! 🎉\n\n"
                "We're thrilled to have you join us in this exciting battle of artificial intelligence! 🤖⚔️🤖\n\n"
                "To get started, please provide a captivating topic of your choice. It can be anything from science, history, entertainment, or any subject that piques your interest! 🌟💡\n\n"
                "Once you've chosen your topic, I'll generate three thought-provoking questions related to it. These questions will be used to rank the performance of the competing chatbots, Claude and GPT, as they go head-to-head in a battle of knowledge and creativity! 🥊🧠\n\n"
                "So, what topic would you like to explore today? Let your imagination run wild and give us a subject that will put these AI marvels to the ultimate test! 🤔💭\n\n"
                "Please enter your topic below:\u200B"
            ),        
            server_bot_dependencies={"GPT-3.5-Turbo": 7, "Claude-3-Sonnet":3})

@stub.function(image=image, secrets=[Secret.from_name("supabase")])
@asgi_app()
def fastapi_app():
    global supabase
    supabase = create_client(os.environ["URL"], os.environ["KEY"])
    bot = ChatbotArenaBot()
    app = fp.make_app(bot, allow_without_key=True)
    return app
