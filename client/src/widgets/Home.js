import React from 'react';
import { Button } from '../components/ui/button';
import './Home.css';

const Home = ({ onNavigate }) => {
  const features = [
    {
      icon: '📊',
      title: 'Risk Assessment',
      description: 'Get Low/Moderate/High risk ratings for suppliers with detailed analysis'
    },
    {
      icon: '🔍',
      title: 'Intelligent Search',
      description: 'Synthetic Signal Retrieval technology for better document matching'
    },
    {
      icon: '📋',
      title: 'Evidence-Based',
      description: 'All risk assessments include supporting documents and references'
    },
    {
      icon: '⚡',
      title: 'Real-time Analysis',
      description: 'Instant risk evaluations with comprehensive reporting'
    },
    {
      icon: '🏢',
      title: 'Supplier Management',
      description: 'Manage and analyze multiple suppliers simultaneously'
    },
    {
      icon: '📈',
      title: 'Trend Analysis',
      description: 'Track risk changes over time with historical data'
    }
  ];

  const stats = [
    { number: '99%', label: 'Accuracy Rate' },
    { number: '< 5s', label: 'Response Time' },
    { number: '50+', label: 'Risk Factors' },
    { number: '24/7', label: 'Availability' }
  ];

  return (
    <div className="home-container">
      <section className="hero-section">
        <div className="hero-content">
          <h1>Welcome to AI Supply Chain Risk Analyzer</h1>
          <p className="hero-subtitle">
            Make informed procurement decisions with AI-powered supplier risk analysis.
            Evaluate financial, operational, and geopolitical risks with evidence-based insights.
          </p>
          <div className="hero-actions">
            <Button size="lg" onClick={() => onNavigate('analysis')}>Get Started</Button>
            <Button variant="outline" size="lg" onClick={() => onNavigate('suppliers')}>View Suppliers</Button>
          </div>
        </div>
        <div className="hero-visual">
          <div className="dashboard-preview">
            <div className="preview-header">
              <span className="risk-badge high">High Risk</span>
              <span className="supplier-id">SUP-22</span>
            </div>
            <div className="preview-content">
              <div className="metric">
                <span className="metric-label">Financial Health</span>
                <div className="metric-bar">
                  <div className="metric-fill low"></div>
                </div>
              </div>
              <div className="metric">
                <span className="metric-label">Geopolitical Risk</span>
                <div className="metric-bar">
                  <div className="metric-fill high"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="features-section">
        <div className="section-header">
          <h2>Powerful Features</h2>
          <p>Advanced AI technology for comprehensive supplier risk analysis</p>
        </div>
        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-card">
              <div className="feature-icon">{feature.icon}</div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="stats-section">
        <div className="stats-grid">
          {stats.map((stat, index) => (
            <div key={index} className="stat-card">
              <div className="stat-number">{stat.number}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="cta-section">
        <div className="cta-content">
          <h2>Ready to Analyze Your Suppliers?</h2>
          <p>Start making data-driven procurement decisions today</p>
          <Button size="lg" onClick={() => onNavigate('analysis')}>Start Risk Analysis</Button>
        </div>
      </section>
    </div>
  );
};

export default Home;
