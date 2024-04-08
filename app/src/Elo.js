import React, { useState, useEffect } from 'react';
import { Paper, Typography, List, ListItem, ListItemText } from '@mui/material';

const EloRatingCalculator = ({ matches, kFactor = 32, defaultRating = 1500 }) => {
  const [eloRatings, setEloRatings] = useState({});

  useEffect(() => {
    const calculateEloRatings = () => {
      const newEloRatings = {};

      matches.forEach(([playerA, playerB, result]) => {
        if (!newEloRatings[playerA]) {
          newEloRatings[playerA] = defaultRating;
        }
        if (!newEloRatings[playerB]) {
          newEloRatings[playerB] = defaultRating;
        }

        const ra = newEloRatings[playerA];
        const rb = newEloRatings[playerB];

        const ea = 1 / (1 + Math.pow(10, (rb - ra) / 400));
        const eb = 1 / (1 + Math.pow(10, (ra - rb) / 400));

        let sa, sb;
        if (result === playerA) {
          sa = 1;
          sb = 0;
        } else if (result === playerB) {
          sa = 0;
          sb = 1;
        } else {
          sa = 0.5;
          sb = 0.5;
        }

        const raNew = ra + kFactor * (sa - ea);
        const rbNew = rb + kFactor * (sb - eb);

        newEloRatings[playerA] = raNew;
        newEloRatings[playerB] = rbNew;
      });

      setEloRatings(newEloRatings);
    };

    calculateEloRatings();
  }, [matches, kFactor, defaultRating]);

  return (
    <Paper elevation={3} style={{ padding: '20px', margin: '20px' }}>
      <Typography variant="h5" component="h2">Elo Ratings:</Typography>
      <List>
        {Object.entries(eloRatings).map(([player, rating]) => (
          <ListItem key={player}>
            <ListItemText primary={`${player}: ${Math.round(rating)}`} />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};

export default EloRatingCalculator;