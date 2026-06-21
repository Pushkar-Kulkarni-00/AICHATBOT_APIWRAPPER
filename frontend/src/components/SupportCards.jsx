import React from 'react';
import './SupportCards.css';

function SupportCards({ intents, onSelectIntent }) {
  return (
    <div className="support-cards-container">
      <div className="welcome-header">
        <h2>Hello! How can we help you today?</h2>
        <p>Select an option below or choose "Other" to ask something specific</p>
      </div>
      
      <div className="cards-grid">
        {intents.map((intent) => (
          <button
            key={intent.code}
            className="support-card"
            onClick={() => onSelectIntent(intent.code)}
          >
            <div className="card-icon">{intent.icon}</div>
            <div className="card-name">{intent.name}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

export default SupportCards;
