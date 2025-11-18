import React, { useState, useEffect } from 'react';
import { getSuppliers } from '../api/api';
import './Suppliers.css';

const Suppliers = () => {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchSuppliers = async () => {
      try {
        const response = await getSuppliers();
        // Create mock supplier data with additional info
        const enrichedSuppliers = response.suppliers.map(id => ({
          id,
          name: `Supplier ${id}`,
          category: ['Technology', 'Manufacturing', 'Services', 'Logistics'][Math.floor(Math.random() * 4)],
          location: ['USA', 'China', 'Germany', 'Japan', 'India'][Math.floor(Math.random() * 5)],
          riskLevel: ['Low', 'Moderate', 'High'][Math.floor(Math.random() * 3)],
          lastAssessment: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toLocaleDateString(),
          documents: Math.floor(Math.random() * 10) + 1
        }));
        setSuppliers(enrichedSuppliers);
      } catch (error) {
        console.error('Error fetching suppliers:', error);
        // Fallback demo data
        const demoSuppliers = ['SUP-11', 'SUP-22', 'SUP-29', 'SUP-45', 'SUP-67'].map(id => ({
          id,
          name: `Supplier ${id}`,
          category: ['Technology', 'Manufacturing', 'Services', 'Logistics'][Math.floor(Math.random() * 4)],
          location: ['USA', 'China', 'Germany', 'Japan', 'India'][Math.floor(Math.random() * 5)],
          riskLevel: ['Low', 'Moderate', 'High'][Math.floor(Math.random() * 3)],
          lastAssessment: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toLocaleDateString(),
          documents: Math.floor(Math.random() * 10) + 1
        }));
        setSuppliers(demoSuppliers);
      } finally {
        setLoading(false);
      }
    };
    fetchSuppliers();
  }, []);

  const filteredSuppliers = suppliers.filter(supplier =>
    supplier.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    supplier.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    supplier.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getRiskBadgeClass = (riskLevel) => {
    switch (riskLevel.toLowerCase()) {
      case 'low': return 'risk-low';
      case 'moderate': return 'risk-moderate';
      case 'high': return 'risk-high';
      default: return 'risk-moderate';
    }
  };

  if (loading) {
    return (
      <div className="suppliers-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading suppliers...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="suppliers-container">
      <div className="suppliers-header">
        <h1>Supplier Management</h1>
        <p>View and manage all suppliers in your risk analysis database</p>
      </div>

      <div className="suppliers-controls">
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search suppliers by name, ID, or category..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <span className="search-icon">🔍</span>
        </div>
        <div className="supplier-stats">
          <span className="stat-item">Total: {suppliers.length}</span>
          <span className="stat-item">High Risk: {suppliers.filter(s => s.riskLevel === 'High').length}</span>
          <span className="stat-item">Active: {suppliers.length}</span>
        </div>
      </div>

      <div className="suppliers-grid">
        {filteredSuppliers.map(supplier => (
          <div key={supplier.id} className="supplier-card">
            <div className="supplier-header">
              <div className="supplier-info">
                <h3 className="supplier-name">{supplier.name}</h3>
                <span className="supplier-id">{supplier.id}</span>
              </div>
              <span className={`risk-badge ${getRiskBadgeClass(supplier.riskLevel)}`}>
                {supplier.riskLevel}
              </span>
            </div>

            <div className="supplier-details">
              <div className="detail-item">
                <span className="detail-label">Category:</span>
                <span className="detail-value">{supplier.category}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Location:</span>
                <span className="detail-value">{supplier.location}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Documents:</span>
                <span className="detail-value">{supplier.documents}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Last Assessment:</span>
                <span className="detail-value">{supplier.lastAssessment}</span>
              </div>
            </div>

            <div className="supplier-actions">
              <button className="action-btn primary">View Details</button>
              <button className="action-btn secondary">Run Analysis</button>
            </div>
          </div>
        ))}
      </div>

      {filteredSuppliers.length === 0 && (
        <div className="no-results">
          <h3>No suppliers found</h3>
          <p>Try adjusting your search criteria</p>
        </div>
      )}
    </div>
  );
};

export default Suppliers;
