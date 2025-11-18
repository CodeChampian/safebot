import React from 'react';
import { Button } from '../components/ui/button';
import './Navigation.css';

const Navigation = ({ currentView, onViewChange }) => {
  const navItems = [
    { id: 'home', label: 'Home', icon: '🏠' },
    { id: 'analysis', label: 'Risk Analysis', icon: '📊' },
    { id: 'suppliers', label: 'Suppliers', icon: '🏢' }
  ];

  return (
    <nav className="main-navigation">
      <div className="nav-brand">
        <h2>AI Supply Chain Risk Analyzer</h2>
      </div>
      <div className="nav-menu">
        {navItems.map(item => (
          <Button
            key={item.id}
            variant={currentView === item.id ? 'default' : 'ghost'}
            onClick={() => onViewChange(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </Button>
        ))}
      </div>
    </nav>
  );
};

export default Navigation;
