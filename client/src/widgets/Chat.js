import React, { useState, useEffect } from 'react';
import RiskQueryInput from './ChatInput';
import { analyzeRisk, getSuppliers } from '../api/api';
import './Chat.css';

const RiskAnalyzer = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [suppliers, setSuppliers] = useState([]);
  const [selectedVendors, setSelectedVendors] = useState([]);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);

  useEffect(() => {
    const fetchSuppliers = async () => {
      try {
        const response = await getSuppliers();
        setSuppliers(response.suppliers || []);
      } catch (error) {
        console.error('Error fetching suppliers:', error);
        setSuppliers([]);
      }
    };
    fetchSuppliers();
  }, []);

  const handleAnalyze = async (query, selectedVendors) => {
    if (!query.trim()) return;

    setIsLoading(true);
    setCurrentAnalysis(null);

    try {
      const response = await analyzeRisk(query, selectedVendors);
      setCurrentAnalysis({
        query,
        selectedVendors,
        ...response
      });
    } catch (error) {
      console.error('Error analyzing risk:', error);
      setCurrentAnalysis({
        query,
        selectedVendors,
        error: "Sorry, I encountered an error. Please try again."
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="risk-analyzer-container">
      <div className="analyzer-header">
        <h2>Supply Chain Risk Analysis</h2>
        <p>Select suppliers and enter your risk assessment query</p>
      </div>

      <RiskQueryInput
        onSendMessage={handleAnalyze}
        disabled={isLoading}
        suppliers={suppliers}
        selectedVendors={selectedVendors}
        setSelectedVendors={setSelectedVendors}
      />

      {isLoading && (
        <div className="loading-indicator">
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <p>Analyzing risk...</p>
        </div>
      )}

      {currentAnalysis && (
        <div className="analysis-result">
          <div className="result-header">
            <h3>Risk Assessment Results</h3>
            <div className="risk-level" data-level={currentAnalysis.risk_level?.toLowerCase()}>
              Risk Level: {currentAnalysis.risk_level}
            </div>
          </div>

          <div className="result-content">
            <div className="query-info">
              <strong>Query:</strong> {currentAnalysis.query}
            </div>
            {currentAnalysis.selectedVendors.length > 0 && (
              <div className="vendors-info">
                <strong>Suppliers Analyzed:</strong> {currentAnalysis.selectedVendors.join(', ')}
              </div>
            )}

            {currentAnalysis.error ? (
              <div className="error-message">
                {currentAnalysis.error}
              </div>
            ) : (
              <>
                <div className="summary">
                  <strong>Summary:</strong>
                  <p>{currentAnalysis.summary}</p>
                </div>

                {currentAnalysis.evidence && currentAnalysis.evidence.length > 0 && (
                  <div className="evidence">
                    <strong>Evidence:</strong>
                    <ul>
                      {currentAnalysis.evidence.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskAnalyzer;
