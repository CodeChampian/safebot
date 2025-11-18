import React, { useState, useRef, useEffect } from 'react';
import './ChatInput.css';

const RiskQueryInput = ({ onSendMessage, disabled, suppliers, selectedVendors, setSelectedVendors }) => {
  const [query, setQuery] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.focus();
    }
  }, [disabled]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !disabled) {
      onSendMessage(query, selectedVendors);
      setQuery('');
    }
  };

  const handleVendorChange = (vendor) => {
    setSelectedVendors(prev =>
      prev.includes(vendor)
        ? prev.filter(v => v !== vendor)
        : [...prev, vendor]
    );
  };

  return (
    <div className="risk-query-container">
      {suppliers.length > 0 && (
        <div className="supplier-selector">
          <h3>Select Suppliers to Analyze</h3>
          <div className="supplier-grid">
            {suppliers.map(vendor => (
              <label key={vendor} className="supplier-checkbox">
                <input
                  type="checkbox"
                  checked={selectedVendors.includes(vendor)}
                  onChange={() => handleVendorChange(vendor)}
                  disabled={disabled}
                />
                <span className="supplier-name">{vendor}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      <div className="query-section">
        <h3>Risk Assessment Query</h3>
        <form onSubmit={handleSubmit} className="query-form">
          <div className="query-input-wrapper">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., Does this supplier show liquidity concerns?"
              disabled={disabled}
              className="query-input"
            />
            <button
              type="submit"
              disabled={!query.trim() || disabled}
              className="analyze-button"
            >
              {disabled ? 'Analyzing...' : 'Analyze Risk'}
            </button>
          </div>
        </form>
        {selectedVendors.length === 0 && suppliers.length > 0 && (
          <p className="helper-text">Tip: Select specific suppliers for targeted analysis, or leave unselected to analyze all available data.</p>
        )}
      </div>
    </div>
  );
};

export default RiskQueryInput;
