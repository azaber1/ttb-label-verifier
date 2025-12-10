import React, { useState } from 'react';
import './App.css';

function App() {
  const [formData, setFormData] = useState({
    brandName: '',
    productClass: '',
    alcoholContent: '',
    netContents: '',
  });
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      // create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);

    if (!image) {
      setError('Please upload a label image');
      setLoading(false);
      return;
    }

    // build form data to send
    const formDataToSend = new FormData();
    formDataToSend.append('image', image);
    formDataToSend.append('brandName', formData.brandName);
    formDataToSend.append('productClass', formData.productClass);
    formDataToSend.append('alcoholContent', formData.alcoholContent);
    formDataToSend.append('netContents', formData.netContents);

    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';
    
    try {
      const response = await fetch(`${API_URL}/api/verify`, {
        method: 'POST',
        body: formDataToSend,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Verification failed');
      }

      setResults(data);
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      brandName: '',
      productClass: '',
      alcoholContent: '',
      netContents: '',
    });
    setImage(null);
    setImagePreview(null);
    setResults(null);
    setError(null);
  };

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <h1>TTB Label Verifier</h1>
          <p>Verify alcohol beverage labels against application form data</p>
        </header>

        <div className="main-content">
          <div className="form-section">
            <form onSubmit={handleSubmit} className="verification-form">
              <div className="form-group">
                <label htmlFor="brandName">
                  Brand Name <span className="required">*</span>
                </label>
                <input
                  type="text"
                  id="brandName"
                  name="brandName"
                  value={formData.brandName}
                  onChange={handleInputChange}
                  required
                  placeholder="e.g., Old Tom Distillery"
                />
              </div>

              <div className="form-group">
                <label htmlFor="productClass">
                  Product Class/Type <span className="required">*</span>
                </label>
                <input
                  type="text"
                  id="productClass"
                  name="productClass"
                  value={formData.productClass}
                  onChange={handleInputChange}
                  required
                  placeholder="e.g., Kentucky Straight Bourbon Whiskey"
                />
              </div>

              <div className="form-group">
                <label htmlFor="alcoholContent">
                  Alcohol Content (ABV) <span className="required">*</span>
                </label>
                <input
                  type="text"
                  id="alcoholContent"
                  name="alcoholContent"
                  value={formData.alcoholContent}
                  onChange={handleInputChange}
                  required
                  placeholder="e.g., 45% or 45"
                />
              </div>

              <div className="form-group">
                <label htmlFor="netContents">
                  Net Contents (Optional)
                </label>
                <input
                  type="text"
                  id="netContents"
                  name="netContents"
                  value={formData.netContents}
                  onChange={handleInputChange}
                  placeholder="e.g., 750 mL or 12 fl oz"
                />
              </div>

              <div className="form-group">
                <label htmlFor="image">
                  Label Image <span className="required">*</span>
                </label>
                <div className="image-upload">
                  <input
                    type="file"
                    id="image"
                    name="image"
                    accept="image/*"
                    onChange={handleImageChange}
                    required
                  />
                  {imagePreview && (
                    <div className="image-preview">
                      <img src={imagePreview} alt="Label preview" />
                    </div>
                  )}
                </div>
              </div>

              <div className="form-actions">
                <button type="submit" disabled={loading} className="submit-btn">
                  {loading ? 'Verifying...' : 'Verify Label'}
                </button>
                <button type="button" onClick={handleReset} className="reset-btn">
                  Reset
                </button>
              </div>
            </form>
          </div>

          {/* Preview Section - Always Visible */}
          <div className="preview-section" data-testid="preview-section">
            <h2>Label Preview</h2>
            <div className="preview-image">
              {imagePreview ? (
                <img src={imagePreview} alt="Label" />
              ) : (
                <div className="preview-placeholder">
                  <p>Upload a label image to see preview</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {error && (
          <div className="error-message">
            <h3>⚠ Error</h3>
            <p>{error}</p>
          </div>
        )}

        {results && (
          <div className="results-section">
            <div className={`results-header ${results.overall_match ? 'success' : 'failure'}`}>
              <h2>
                {results.overall_match ? '✓ Label Verification Successful' : '✗ Label Verification Failed'}
              </h2>
              <p>
                {results.overall_match
                  ? 'The label matches the form data. All required information is consistent.'
                  : 'The label does not match the form. Please review the discrepancies below.'}
              </p>
            </div>

            <div className="checks-list">
              {results.checks.map((check, index) => (
                <div key={index} className={`check-item ${check.matched ? 'matched' : 'mismatched'}`}>
                  <div className="check-icon">
                    {check.matched ? '✓' : '✗'}
                  </div>
                  <div className="check-content">
                    <h4>{check.field}</h4>
                    <p>{check.message}</p>
                  </div>
                </div>
              ))}
            </div>

            {results.extracted_text_preview && (
              <div className="extracted-text">
                <h3>Extracted Text Preview</h3>
                <p className="text-preview">{results.extracted_text_preview}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
