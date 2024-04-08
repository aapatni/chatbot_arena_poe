import "./App.css";
import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import {
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Paper,
} from "@mui/material";
import Elo from "./Elo.js"; 

const supabaseUrl = "https://gvvfniijngcyqnwvrbal.supabase.co";
const supabaseAnonKey =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd2dmZuaWlqbmdjeXFud3ZyYmFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDcxNTc5NTksImV4cCI6MjAyMjczMzk1OX0.PPnrMeW0K4Pwri-sgpG5U6F4fqu8KsxUvxOX3_fk_60";

const supabase = createClient(supabaseUrl, supabaseAnonKey);

function App() {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      console.log("A");
      let { data: poebotData, error } = await supabase.from("poebot").select("*");
      console.log("B");

      if (error) {
        console.error("error", error);
      } else {
        // Process the winner field according to the new rules
        const processedData = poebotData.map((row) => {
          if (row.winner === null) {
            row.winner = "tie";
          } else if (row.winner === false) {
            row.winner = row.bot_a;
          } else if (row.winner === true) {
            row.winner = row.bot_b;
          }
          return row;
        });
        // Sort the data by created_at timestamp
        processedData.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        setData(processedData);
      }
      console.log(poebotData);
    };

    fetchData();
  }, []);

  const columns = [
    // { id: "id", label: "ID", minWidth: 150 },
    // { id: "message_id", label: "Message ID", minWidth: 150 },
    { id: "topic", label: "Topic" },
    { id: "winner", label: "Winner" },
    { id: "bot_a", label: "Bot A" },
    { id: "bot_b", label: "Bot B" },
    { id: "q1", label: "Question 1" },
    { id: "q2", label: "Question 2" },
    { id: "q3", label: "Question 3" },
  ];

  return (
    <div
      className="App"
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
      }}
    >
      <header className="App-header" style={{ width: "90%" }}>
        <h2 style={{ textAlign: "center" }}>ChatBot Arena Rankings</h2>
        <Elo matches={data.map(row => [row.bot_a, row.bot_b, row.winner])} />
        <TableContainer component={Paper} style={{ maxHeight: "50vh", width: "100%", backgroundColor: "#f0f0f0" }}>
          <Table stickyHeader aria-label="sticky table">
            <TableHead>
              <TableRow>
                {columns.map((column) => (
                  <TableCell
                    key={column.id}
                    align="center"
                    style={{ minWidth: column.minWidth }}
                  >
                    {column.label}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {data.map((row) => {
                return (
                  <TableRow hover role="checkbox" tabIndex={-1} key={row.code}>
                    {columns.map((column) => {
                      const value = row[column.id];
                      return (
                        <TableCell key={column.id} align="center">
                          {value}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </header>
    </div>
  );
}

export default App;
