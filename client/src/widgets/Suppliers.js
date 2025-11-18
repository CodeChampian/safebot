import React, { useState, useEffect } from 'react';
import { getAllSuppliers, createSupplier, uploadSupplierDocument } from '../api/api';
import { Button } from '../components/ui/button.jsx';
import { Input } from '../components/ui/input.jsx';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card.jsx';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog.jsx';
import { Label } from '../components/ui/label.jsx';
import './Suppliers.css';

const Suppliers = () => {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    location: '',
    contact_email: '',
    contact_phone: '',
    description: ''
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const fetchSuppliers = async () => {
    try {
      const response = await getAllSuppliers();
      setSuppliers(response.suppliers);
    } catch (error) {
      console.error('Error fetching suppliers:', error);
      setSuppliers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSupplier = async (e) => {
    e.preventDefault();
    setErrors({});

    // Basic validation
    if (!formData.name.trim() || !formData.category.trim() || !formData.location.trim()) {
      setErrors({ general: 'Please fill in all required fields.' });
      return;
    }

    try {
      const response = await createSupplier({
        name: formData.name.trim(),
        category: formData.category.trim(),
        location: formData.location.trim(),
        contact_email: formData.contact_email.trim() || null,
        contact_phone: formData.contact_phone.trim() || null,
        description: formData.description.trim() || null
      });

      // Add the new supplier to the list
      setSuppliers(prev => [...prev, response.supplier]);

      // Reset form and close dialog
      setFormData({
        name: '',
        category: '',
        location: '',
        contact_email: '',
        contact_phone: '',
        description: ''
      });
      setIsCreateDialogOpen(false);
    } catch (error) {
      console.error('Error creating supplier:', error);
      setErrors({ general: 'Failed to create supplier. Please try again.' });
    }
  };

  const handleFileUpload = async (supplierId, file) => {
    setIsUploading(true);
    try {
      await uploadSupplierDocument(supplierId, file);
      // Refresh suppliers to get updated document count
      fetchSuppliers();
    } catch (error) {
      console.error('Error uploading document:', error);
    } finally {
      setIsUploading(false);
    }
  };

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
      <div className="suppliers-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Supplier Management</h1>
          <p>View and manage all suppliers in your risk analysis database</p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>Add New Supplier</Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Create New Supplier</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateSupplier} className="space-y-4">
              {errors.general && (
                <div className="text-red-600 text-sm bg-red-50 p-3 rounded">
                  {errors.general}
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Company Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter company name"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="category">Category *</Label>
                  <Input
                    id="category"
                    value={formData.category}
                    onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
                    placeholder="e.g., Technology, Manufacturing"
                    required
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="location">Location *</Label>
                <Input
                  id="location"
                  value={formData.location}
                  onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                  placeholder="Country or region"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="contact_email">Email</Label>
                  <Input
                    id="contact_email"
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) => setFormData(prev => ({ ...prev, contact_email: e.target.value }))}
                    placeholder="contact@company.com"
                  />
                </div>

                <div>
                  <Label htmlFor="contact_phone">Phone</Label>
                  <Input
                    id="contact_phone"
                    value={formData.contact_phone}
                    onChange={(e) => setFormData(prev => ({ ...prev, contact_phone: e.target.value }))}
                    placeholder="+1-555-0123"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Brief description of the supplier..."
                  className="flex min-h-[80px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-800 dark:bg-slate-950 dark:ring-offset-slate-950 dark:placeholder:text-slate-400 dark:focus-visible:ring-slate-300"
                  rows="3"
                />
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsCreateDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit">
                  Create Supplier
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
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
          <Card key={supplier.id} className="supplier-card">
            <CardHeader className="supplier-header">
              <div className="supplier-info">
                <CardTitle className="supplier-name">{supplier.name}</CardTitle>
                <span className="supplier-id">{supplier.id}</span>
              </div>
              <span className={`risk-badge ${getRiskBadgeClass(supplier.riskLevel)}`}>
                {supplier.riskLevel}
              </span>
            </CardHeader>

            <CardContent className="supplier-details">
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
                <span className="detail-value">{supplier.document_count}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Last Assessment:</span>
                <span className="detail-value">{new Date(supplier.last_assessment).toLocaleDateString()}</span>
              </div>
              {supplier.contact_email && (
                <div className="detail-item">
                  <span className="detail-label">Email:</span>
                  <span className="detail-value">{supplier.contact_email}</span>
                </div>
              )}
            </CardContent>

            <div className="supplier-actions">
              <Button
                className="action-btn primary"
                onClick={() => {
                  const input = document.createElement('input');
                  input.type = 'file';
                  input.accept = '.pdf,.doc,.docx,.txt';
                  input.onchange = (e) => {
                    if (e.target.files[0]) {
                      handleFileUpload(supplier.id, e.target.files[0]);
                    }
                  };
                  input.click();
                }}
                disabled={isUploading}
              >
                {isUploading ? 'Uploading...' : 'Upload Document'}
              </Button>
              <Button className="action-btn secondary">Run Analysis</Button>
            </div>
          </Card>
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
