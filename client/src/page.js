import React, { useState, useEffect } from 'react';
import './ImageAnalysis.css';
import './VisualReasoningApp.css';

// Pattern Display Component
const PatternDisplay = ({ pattern }) => {
  // Convert rating to number of stars (1 = 5 stars, 0.8 = 4 stars, etc.)
  const getStarCount = (rating) => {
    if (rating >= 1) return 5;
    if (rating >= 0.8) return 4;
    if (rating >= 0.6) return 3;
    if (rating >= 0.4) return 2;
    if (rating >= 0.2) return 1;
    return 0;
  };

  const starCount = getStarCount(pattern.rating);

  return (
    <div className="pattern-card">
      {/* Image Section */}
      <div className="pattern-image">
        <img 
          src={`http://localhost:8000/processed_images/${pattern.image_name}`}
          alt={pattern.scene_type}
        />
      </div>

      {/* Scene Type */}
      <div className="pattern-type">{pattern.scene_type}</div>

      {/* Inference Section */}
      <div className="pattern-inference">
        {pattern.inference}
      </div>

      {/* Rating Section */}
      <div className="pattern-rating">
        {[...Array(5)].map((_, index) => (
          <span key={index} className={`star ${index < starCount ? "filled" : "empty"}`}>
            ★
          </span>
        ))}
      </div>

      {/* Relationships Section */}
      <div className="pattern-relationships-container">
        {pattern.typical_relationships && pattern.typical_relationships.length > 0 && (
          <div className="pattern-relationships">
            <h4>Common Patterns:</h4>
            <ul>
              {pattern.typical_relationships.map((rel, index) => (
                <li key={`typical-${index}`}>
                  <span className="relationship-subject">{rel.subject}</span>
                  <span className="relationship-spatial">{rel.spatial}</span>
                  <span className="relationship-object">{rel.object}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {pattern.atypical_relationships && pattern.atypical_relationships.length > 0 && (
          <div className="pattern-relationships unusual">
            <h4>Unusual Patterns:</h4>
            <ul>
              {pattern.atypical_relationships.map((rel, index) => (
                <li key={`atypical-${index}`}>
                  <span className="relationship-subject">{rel.subject}</span>
                  <span className="relationship-spatial">{rel.spatial}</span>
                  <span className="relationship-object">{rel.object}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

// Format analysis text with special styling for numbered points
const formatAnalysisText = (text) => {
  if (!text) return "";
  
  // Replace numbered points with styled versions
  return text.replace(/(\d+\.\s)([^\n]+)/g, (match, number, content) => {
    return `<div class="analysis-point"><span class="point-number">${number}</span>${content}</div>`;
  });
};

const Page = () => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [textInput, setTextInput] = useState('');
  const [basicAnalysis, setBasicAnalysis] = useState(null);
  const [enhancedAnalysis, setEnhancedAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [basicRating, setBasicRating] = useState(0);
  const [basicFeedback, setBasicFeedback] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [existingFiles, setExistingFiles] = useState([]);
  const [filename, setFilename] = useState('');
  const [analysisStage, setAnalysisStage] = useState('initial');
  const [sceneContext, setSceneContext] = useState(null);
  const [relevantPatterns, setRelevantPatterns] = useState(null);
  const [relationshipKeys, setRelationshipKeys] = useState(null);

  // Fetch list of existing files when component mounts
  useEffect(() => {
    fetch('http://localhost:8000/files')
      .then(response => response.json())
      .then(data => {
        if (data.files) {
          setExistingFiles(data.files);
        }
      })
      .catch(err => console.error('Error fetching files:', err));
  }, []);

  const handleFilenameChange = (event) => {
    setFilename(event.target.value);
    setBasicAnalysis(null);
    setEnhancedAnalysis(null);
    setError(null);
  };

  const handleImageSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
      setImagePreview(URL.createObjectURL(file));
      setBasicAnalysis(null);
      setEnhancedAnalysis(null);
      setError(null);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedImage(file);
      setImagePreview(URL.createObjectURL(file));
      setBasicAnalysis(null);
      setEnhancedAnalysis(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!filename) return;

    setLoading(true);
    setError(null);
    setBasicAnalysis(null);
    setEnhancedAnalysis(null);
    setAnalysisStage('basic');

    try {
      // First get basic analysis
      const response = await fetch('http://localhost:8000/inference/basic', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setBasicAnalysis(data.text);
      setSceneContext(data.scene_analysis);
      
    } catch (err) {
      setError('Failed to analyze. Please try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedbackSubmit = async () => {
    if (!basicAnalysis) return;
    
    setSubmitting(true);
    
    try {
      // First submit feedback
      console.log("Submitting feedback with:", {
        filename,
        basicRating,
        basicFeedback,
        sceneContext
      });

      const response = await fetch('http://localhost:8000/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: filename,
          basicRating,
          basicFeedback,
          sceneContext
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.log(filename);
        console.error("Feedback submission failed:", errorText);
        throw new Error(`Feedback submission failed: ${errorText}`);
      }

      const feedbackData = await response.json();
      const feedbackId = feedbackData.feedback_id;

      console.log("Feedback submitted successfully, requesting enhanced analysis with:", {
        filename,
        feedback_id: feedbackId
      });

      // After successful feedback submission, get enhanced analysis
      const enhancedResponse = await fetch('http://localhost:8000/inference/enhanced', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          filename,
          scene_analysis: sceneContext,
          feedback_id: feedbackId
        })
      });

      if (!enhancedResponse.ok) {
        const errorText = await enhancedResponse.text();
        console.error("Enhanced analysis failed:", errorText);
        throw new Error(`Enhanced analysis failed: ${errorText}`);
      }

      const enhancedData = await enhancedResponse.json();
      setEnhancedAnalysis(enhancedData.text);
      setRelevantPatterns(enhancedData.relevant_patterns);
      setRelationshipKeys(enhancedData.relationship_keys);
      setAnalysisStage('enhanced');
      
    } catch (err) {
      setError(`Failed to submit feedback or get enhanced analysis: ${err.message}`);
      console.error('Detailed error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const resetState = () => {
    setSelectedImage(null);
    setImagePreview(null);
    setFilename('');
    setTextInput('');
    setBasicAnalysis(null);
    setEnhancedAnalysis(null);
    setError(null);
    setBasicRating(0);
    setBasicFeedback('');
    setRelationshipKeys(null);
  };

  const StarRating = ({ rating, setRating }) => {
    return (
      <div className="flex items-center justify-center space-x-1 my-2">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            className="focus:outline-none"
            onClick={() => setRating(star)}
          >
            <svg
              className={`w-8 h-8 ${
                star <= rating ? 'text-yellow-300' : 'text-gray-400'
              }`}
              fill="currentColor"
              viewBox="0 0 20 20"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          </button>
        ))}
        <span className="ml-2 text-gray-300">({rating}/5)</span>
      </div>
    );
  };

  return (
    <div className="visual-reasoning-app">
      {/* Magical particles for ethereal effect */}
      <div className="magical-particles">
        {[...Array(20)].map((_, i) => (
          <div key={i} className={`particle particle-${i % 5}`}></div>
        ))}
      </div>

      <div className="app-container">
        <header className="app-header">
          <h1>Visual Reasoning</h1>
          <div className="subtitle">Discover the hidden patterns in your images</div>
        </header>

        {error && <div className="error-message">{error}</div>}

        {analysisStage === 'initial' && (
          <div className="initial-stage">
            <div className="image-selection-container">
              <div className="selection-methods">
                <div className="selection-method">
                  <h3>Choose from existing images</h3>
                  <select
                    className="file-select"
                    value={filename}
                    onChange={handleFilenameChange}
                    disabled={loading}
                  >
                    <option value="">Select an image...</option>
                    {existingFiles.map(file => (
                      <option key={file} value={file}>{file}</option>
                    ))}
                  </select>
                </div>

                <div className="selection-divider">
                  <span>or</span>
                </div>

                <div className="selection-method">
                  <h3>Upload a new image</h3>
                  <div 
                    className={`dropzone ${imagePreview ? 'active' : ''}`}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleDrop}
                  >
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageSelect}
                      id="file-input"
                      className="hidden"
                    />
                    <label htmlFor="file-input" className="cursor-pointer">
                      {imagePreview ? (
                        <div className="image-preview">
                          <img 
                            src={imagePreview} 
                            alt="Preview" 
                            style={{ maxWidth: '300px', maxHeight: '300px', objectFit: 'contain' }}
                          />
                          <button 
                            className="remove-button"
                            onClick={resetState}
                          >
                            Remove
                          </button>
                        </div>
                      ) : (
                        <div>
                          <p>Drag & drop an image here, or click to select</p>
                          <button className="browse-button">Browse Files</button>
                        </div>
                      )}
                    </label>
                  </div>
                </div>
              </div>

              {(filename || imagePreview) && (
                <div className="image-preview-container">
                  <h3>Selected Image</h3>
                  <div className="image-preview">
                    <img
                      src={imagePreview || `http://localhost:8000/images/${filename}`}
                      alt="Preview"
                      style={{ maxWidth: '300px', maxHeight: '300px', objectFit: 'contain' }}
                    />
                  </div>
                  <button 
                    className="analyze-button" 
                    onClick={handleAnalyze} 
                    disabled={loading || (!filename && !imagePreview)}
                  >
                    {loading ? <span className="loading-spinner"></span> : "Analyze Image"}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {analysisStage === 'basic' && basicAnalysis && (
          <div className="basic-stage">
            <div className="analysis-container">
              <div className="image-column">
                <h3>Original Image</h3>
                <div className="image-display">
                  <img 
                    src={`http://localhost:8000/processed_images/${filename}`}
                    alt="Selected scene"
                    style={{ maxWidth: '300px', maxHeight: '300px', objectFit: 'contain' }}
                  />
                </div>
              </div>

              <div className="analysis-column">
                <h3>Basic Analysis (with extracted relationships)</h3>
                <div 
                  className="analysis-text"
                  dangerouslySetInnerHTML={{ __html: formatAnalysisText(basicAnalysis) }}
                />

                <div className="feedback-section">
                  <h3>How helpful was this analysis?</h3>
                  <StarRating rating={basicRating} setRating={setBasicRating} />

                  <div className="feedback-input">
                    <label htmlFor="feedback">Additional Feedback (optional):</label>
                    <textarea
                      id="feedback"
                      value={basicFeedback}
                      onChange={(e) => setBasicFeedback(e.target.value)}
                      placeholder="Share your thoughts on the analysis..."
                      rows={4}
                    />
                  </div>

                  <button
                    className="submit-button"
                    onClick={handleFeedbackSubmit}
                    disabled={submitting || basicRating === 0}
                  >
                    {submitting ? <span className="loading-spinner"></span> : "Submit & Get Enhanced Analysis"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {analysisStage === 'enhanced' && enhancedAnalysis && (
          <div className="enhanced-stage">
            <div className="enhanced-container">
              {/* Original Image Section */}
              <div className="original-image-section">
                <h3>Original Image</h3>
                <div className="image-display">
                  <img 
                    src={`http://localhost:8000/processed_images/${filename}`}
                    alt="Selected scene"
                    style={{ maxWidth: '100%', height: 'auto', objectFit: 'contain' }}
                  />
                </div>
              </div>

              {/* Analysis Comparison Section */}
              <div className="analysis-comparison">
                {/* Basic Analysis Column */}
                <div className="basic-analysis-column">
                  <h3>Basic Analysis (with extracted relationships)</h3>
                  <div 
                    className="analysis-text"
                    dangerouslySetInnerHTML={{ __html: formatAnalysisText(basicAnalysis) }}
                  />
                </div>

                {/* Enhanced Analysis Column */}
                <div className="enhanced-analysis-column">
                  <h3>Enhanced Analysis (with learned patterns from relationships)</h3>
                  <div 
                    className="analysis-text"
                    dangerouslySetInnerHTML={{ __html: formatAnalysisText(enhancedAnalysis) }}
                  />
                </div>
              </div>

              {/* Relationship Keys Section */}
              {relationshipKeys && relationshipKeys.length > 0 && (
                <div className="relationship-keys-section">
                  <h3>Relationships derived from the Image</h3>
                  <div className="relationship-keys-container">
                    {relationshipKeys.map((key, index) => {
                      const [subject, spatial, state, functional, contextual, obj] = key.split('-');
                      return (
                        <div key={index} className="relationship-key-card">
                          <div className="key-components">
                            <span className="key-subject">{subject}</span>
                            <span className="key-spatial">{spatial}</span>
                            <span className="key-state">{state}</span>
                            <span className="key-functional">{functional}</span>
                            <span className="key-contextual">{contextual}</span>
                            <span className="key-object">{obj}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Patterns Section */}
              {relevantPatterns && relevantPatterns.length > 0 && (
                <div className="patterns-section">
                  <h3>Images from DB used to enhance the analysis(Relevant Patterns)</h3>
                  <div className="patterns-container">
                    {relevantPatterns.map((pattern, index) => (
                      <PatternDisplay key={index} pattern={pattern} />
                    ))}
                  </div>
                </div>
              )}

              <button className="analyze-another-button" onClick={resetState}>
                Analyze Another Image
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const ImagePreview = ({ file }) => {
  const [preview, setPreview] = useState('');

  useEffect(() => {
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const MAX_SIZE = 300;
        
        let width = img.width;
        let height = img.height;

        if (width > height) {
          if (width > MAX_SIZE) {
            height *= MAX_SIZE / width;
            width = MAX_SIZE;
          }
        } else {
          if (height > MAX_SIZE) {
            width *= MAX_SIZE / height;
            height = MAX_SIZE;
          }
        }

        canvas.width = width;
        canvas.height = height;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);
        
        setPreview(canvas.toDataURL('image/jpeg'));
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  }, [file]);

  return preview ? (
    <img 
      src={preview} 
      alt="Preview" 
      style={{ 
        maxWidth: '300px',
        maxHeight: '300px',
        objectFit: 'contain'
      }} 
    />
  ) : null;
};

export default Page;