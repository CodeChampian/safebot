import React, { useState, useEffect } from 'react';
import { getAllSuppliers, createSupplier, updateSupplier, uploadSupplierDocument, getSupplierDocuments, deleteSupplierDocument } from '../api/api';
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
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState(null);
  const [isDocumentsDialogOpen, setIsDocumentsDialogOpen] = useState(false);
  const [documentsViewSupplier, setDocumentsViewSupplier] = useState(null);
  const [supplierDocuments, setSupplierDocuments] = useState([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    location: '',
    contact_email: '',
    contact_phone: '',
    description: ''
  });
  const [editFormData, setEditFormData] = useState({
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

  const handleActiveToggle = async (supplierId, currentActive) => {
    try {
      // Prepare update data with all current supplier data plus flipped active
      const supplier = suppliers.find(s => s.id === supplierId);
      if (supplier) {
        const updateData = {
          name: supplier.name,
          category: supplier.category,
          location: supplier.location,
          contact_email: supplier.contact_email,
          contact_phone: supplier.contact_phone,
          description: supplier.description,
          active: !currentActive // Toggle active status
        };

        await updateSupplier(supplierId, updateData);
        // Refresh suppliers to reflect the change
        fetchSuppliers();
      }
    } catch (error) {
      console.error('Error toggling active status:', error);
    }
  };

  const handleEditSupplier = async (e) => {
    e.preventDefault();
    setErrors({});

    // Basic validation
    if (!editFormData.name.trim() || !editFormData.category.trim() || !editFormData.location.trim()) {
      setErrors({ general: 'Please fill in all required fields.' });
      return;
    }

    try {
      const updateData = {
        name: editFormData.name.trim(),
        category: editFormData.category.trim(),
        location: editFormData.location.trim(),
        contact_email: editFormData.contact_email.trim() || null,
        contact_phone: editFormData.contact_phone.trim() || null,
        description: editFormData.description.trim() || null,
        active: editingSupplier.active // Keep current active status
      };

      await updateSupplier(editingSupplier.id, updateData);

      // Refresh suppliers to reflect the changes
      fetchSuppliers();

      // Close dialog
      setIsEditDialogOpen(false);
      setEditingSupplier(null);
    } catch (error) {
      console.error('Error updating supplier:', error);
      setErrors({ general: 'Failed to update supplier. Please try again.' });
    }
  };

  const openEditDialog = (supplier) => {
    setEditingSupplier(supplier);
    setEditFormData({
      name: supplier.name || '',
      category: supplier.category || '',
      location: supplier.location || '',
      contact_email: supplier.contact_email || '',
      contact_phone: supplier.contact_phone || '',
      description: supplier.description || ''
    });
    setIsEditDialogOpen(true);
  };

  const handleViewDocuments = async (supplier) => {
    setDocumentsViewSupplier(supplier);
    setLoadingDocuments(true);
    setSelectedDocument(null);
    try {
      const response = await getSupplierDocuments(supplier.id);
      setSupplierDocuments(response.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
      setSupplierDocuments([]);
    } finally {
      setLoadingDocuments(false);
    }
    setIsDocumentsDialogOpen(true);
  };

  const selectDocument = (document) => {
    setSelectedDocument(document);
  };

  const filteredSuppliers = suppliers.filter(supplier =>
    supplier.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    supplier.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    supplier.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDeleteDocument = async () => {
    if (!documentToDelete || !documentsViewSupplier) return;

    try {
      await deleteSupplierDocument(documentsViewSupplier.id, documentToDelete.id);

      // Remove document from local state
      setSupplierDocuments(prev => prev.filter(doc => doc.id !== documentToDelete.id));

      // Clear selected document if it was the deleted one
      if (selectedDocument && selectedDocument.id === documentToDelete.id) {
        setSelectedDocument(null);
      }

      // Refresh suppliers to update document count
      fetchSuppliers();

      setIsDeleteDialogOpen(false);
      setDocumentToDelete(null);
    } catch (error) {
      console.error('Error deleting document:', error);
    }
  };

  const confirmDeleteDocument = (document) => {
    setDocumentToDelete(document);
    setIsDeleteDialogOpen(true);
  };

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
        <Button onClick={() => setIsCreateDialogOpen(true)}>Add New Supplier</Button>
      </div>

      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
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
                className="flex min-h-[80px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
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

      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Edit Supplier</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleEditSupplier} className="space-y-4">
            {errors.general && (
              <div className="text-red-600 text-sm bg-red-50 p-3 rounded">
                {errors.general}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit-name">Company Name *</Label>
                <Input
                  id="edit-name"
                  value={editFormData.name}
                  onChange={(e) => setEditFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter company name"
                  required
                />
              </div>

              <div>
                <Label htmlFor="edit-category">Category *</Label>
                <Input
                  id="edit-category"
                  value={editFormData.category}
                  onChange={(e) => setEditFormData(prev => ({ ...prev, category: e.target.value }))}
                  placeholder="e.g., Technology, Manufacturing"
                  required
                />
              </div>
            </div>

            <div>
              <Label htmlFor="edit-location">Location *</Label>
              <Input
                id="edit-location"
                value={editFormData.location}
                onChange={(e) => setEditFormData(prev => ({ ...prev, location: e.target.value }))}
                placeholder="Country or region"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit-contact_email">Email</Label>
                <Input
                  id="edit-contact_email"
                  type="email"
                  value={editFormData.contact_email}
                  onChange={(e) => setEditFormData(prev => ({ ...prev, contact_email: e.target.value }))}
                  placeholder="contact@company.com"
                />
              </div>

              <div>
                <Label htmlFor="edit-contact_phone">Phone</Label>
                <Input
                  id="edit-contact_phone"
                  value={editFormData.contact_phone}
                  onChange={(e) => setEditFormData(prev => ({ ...prev, contact_phone: e.target.value }))}
                  placeholder="+1-555-0123"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="edit-description">Description</Label>
              <textarea
                id="edit-description"
                value={editFormData.description}
                onChange={(e) => setEditFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Brief description of the supplier..."
                className="flex min-h-[80px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                rows="3"
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsEditDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit">
                Update Supplier
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Document Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>Confirm Delete</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-center">
              Are you sure you want to delete the file "{documentToDelete?.filename}"?
            </p>
            <p className="text-sm text-gray-600 text-center">
              This action cannot be undone.
            </p>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsDeleteDialogOpen(false);
                setDocumentToDelete(null);
              }}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={handleDeleteDocument}
            >
              Delete File
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Documents Viewer Modal */}
      {isDocumentsDialogOpen && (
        <div className="documents-dialog">
          <div className="documents-dialog-content">
            <div className="mb-4">
              <h3 className="text-lg font-semibold">
                {documentsViewSupplier ? `Documents for ${documentsViewSupplier.name}` : 'Documents'}
              </h3>
            </div>
            <div className="documents-viewer">
              <div className="documents-sidebar">
                <div className="documents-header">
                  <h4>Files ({supplierDocuments.length})</h4>
                </div>
                <div className="documents-list">
                  {loadingDocuments ? (
                    <div className="loading-documents">
                      <div className="loading-spinner"></div>
                      <p>Loading documents...</p>
                    </div>
                  ) : supplierDocuments.length === 0 ? (
                    <div className="no-documents">
                      <p>No documents found</p>
                    </div>
                  ) : (
                    supplierDocuments.map((doc, index) => (
                      <div
                        key={doc.id || index}
                        className={`document-item ${selectedDocument && selectedDocument.id === doc.id ? 'selected' : ''}`}
                        onClick={() => selectDocument(doc)}
                      >
                        <div className="document-icon">
                          {doc.filename?.toLowerCase().endsWith('.pdf') ? '📄' :
                           doc.filename?.toLowerCase().endsWith('.docx') ? '📝' :
                           doc.filename?.toLowerCase().endsWith('.doc') ? '📝' :
                           doc.filename?.toLowerCase().endsWith('.txt') ? '📋' :
                           doc.filename?.toLowerCase().endsWith('.png') ? '🖼️' :
                           doc.filename?.toLowerCase().endsWith('.jpg') ? '🖼️' :
                           doc.filename?.toLowerCase().endsWith('.jpeg') ? '🖼️' : '📎'}
                        </div>
                        <div className="document-info">
                          <div className="document-name" title={doc.filename}>
                            {doc.filename || 'Unnamed file'}
                          </div>
                          <div className="document-date">
                            {new Date(doc.uploaded_at || doc.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
              <div className="documents-preview">
                {selectedDocument ? (
                  <div className="preview-container">
                    <div className="preview-header">
                      <h4>{selectedDocument.filename || 'Document Preview'}</h4>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(selectedDocument.url || selectedDocument.file_url, '_blank')}
                          title="Download file"
                        >
                          📥
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => confirmDeleteDocument(selectedDocument)}
                          title="Delete file"
                        >
                          🗑️
                        </Button>
                      </div>
                    </div>
                    <div className="preview-content">
                      {selectedDocument.filename?.toLowerCase().endsWith('.pdf') ? (
                        <iframe
                          src={selectedDocument.url}
                          className="pdf-preview"
                          title={selectedDocument.filename}
                        />
                      ) : selectedDocument.filename?.toLowerCase().endsWith('.docx') ||
                          selectedDocument.filename?.toLowerCase().endsWith('.doc') ? (
                        <div className="docx-preview-container" style={{ width: '100%', height: '100%' }}>
                          <iframe
                            src={`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/documents/${selectedDocument.id}/preview`}
                            style={{
                              width: '100%',
                              height: '100%',
                              border: 'none',
                              borderRadius: '4px'
                            }}
                            title={`${selectedDocument.filename} Preview`}
                            onLoad={(e) => {
                              // Hide any loading indicator or show success
                              console.log('DOCX preview loaded successfully');
                            }}
                            onError={(e) => {
                              // Fallback to download if preview fails
                              e.target.style.display = 'none';
                              const fallback = e.target.parentNode.querySelector('.docx-fallback');
                              if (fallback) fallback.style.display = 'flex';
                            }}
                          />
                          {/* Fallback UI for when preview fails */}
                          <div className="docx-fallback" style={{
                            display: 'none',
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            textAlign: 'center'
                          }}>
                            <div className="preview-placeholder">
                              <div className="file-icon-large">📝</div>
                              <p>Preview not available</p>
                              <Button
                                onClick={() => window.open(selectedDocument.url, '_blank')}
                              >
                                Download Document
                              </Button>
                            </div>
                          </div>
                        </div>
                      ) : selectedDocument.filename?.toLowerCase().endsWith('.png') ||
                          selectedDocument.filename?.toLowerCase().endsWith('.jpg') ||
                          selectedDocument.filename?.toLowerCase().endsWith('.jpeg') ? (
                        <img
                          src={selectedDocument.url}
                          alt={selectedDocument.filename}
                          className="image-preview"
                          style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                        />
                      ) : selectedDocument.filename?.toLowerCase().endsWith('.txt') ? (
                        <pre className="text-preview">
                          {/* For text files, we would fetch the content and display it */}
                          Text file content would be displayed here
                        </pre>
                      ) : (
                        <div className="unsupported-preview">
                          <div className="preview-placeholder">
                            <div className="file-icon-large">📎</div>
                            <p>This file type requires download to view</p>
                            <Button
                              onClick={() => window.open(selectedDocument.url, '_blank')}
                            >
                              Download File
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="no-preview">
                    <div className="preview-placeholder">
                      <div className="file-icon-large">📁</div>
                      <p>Select a document to preview</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
            <div className="flex justify-end mt-4 pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsDocumentsDialogOpen(false)}
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

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
          <span className="stat-item">Active: {suppliers.filter(s => s.active).length}</span>
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
              <div className="supplier-header-right">
                <Button
                  className="edit-btn"
                  variant="outline"
                  size="sm"
                  onClick={() => openEditDialog(supplier)}
                  title="Edit supplier"
                >
                  ✏️
                </Button>
              </div>
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
              <div className="detail-item">
                <span className="detail-label">Status:</span>
                <span
                  className={`status-text ${supplier.active ? 'status-active' : 'status-inactive'}`}
                  onClick={() => handleActiveToggle(supplier.id, supplier.active)}
                >
                  {supplier.active ? 'Active' : 'Inactive'}
                </span>
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
                  input.accept = '.pdf,.docx,.png,.jpg,.jpeg';
                  input.multiple = true;
                  input.onchange = async (e) => {
                    const files = Array.from(e.target.files);
                    if (files.length > 0) {
                      for (const file of files) {
                        await handleFileUpload(supplier.id, file);
                      }
                    }
                  };
                  input.click();
                }}
                disabled={isUploading}
              >
                {isUploading ? 'Uploading...' : 'Upload Document'}
              </Button>
              <Button
                className="action-btn tertiary"
                onClick={() => handleViewDocuments(supplier)}
                title="View documents"
              >
                View Documents
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
