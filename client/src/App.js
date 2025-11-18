import React, { useState } from 'react';
import Navigation from './widgets/Navigation';
import RiskAnalyzer from './widgets/Chat';
import Home from './widgets/Home';
import Suppliers from './widgets/Suppliers';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('home');

  const renderView = () => {
    switch (currentView) {
      case 'home':
        return <Home onNavigate={setCurrentView} />;
      case 'analysis':
        return <RiskAnalyzer />;
      case 'suppliers':
        return <Suppliers />;
      default:
        return <Home onNavigate={setCurrentView} />;
    }
  };

  return (
    <div className="App">
      <Navigation currentView={currentView} onViewChange={setCurrentView} />
      <main className="main-content">
        {renderView()}
      </main>
    </div>
  );
}

export default App;
