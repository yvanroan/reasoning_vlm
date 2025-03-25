import React, { useState, useEffect } from 'react';
import './ImageAnalysis.css';

const ImageAnalysis = () => {
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

  // Fetch list of existing files when component mounts
  useEffect(() => {
    fetch('http://localhost:5000/files')
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
      const response = await fetch('http://localhost:5000/inference/basic', {
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
        basicFeedback
      });

      const response = await fetch('http://localhost:5000/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: filename,
          basicRating,
          basicFeedback,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Feedback submission failed:", errorText);
        throw new Error(`Feedback submission failed: ${errorText}`);
      }

      console.log("Feedback submitted successfully, requesting enhanced analysis with:", {
        filename,
        scene_analysis: sceneContext
      });

      // After successful feedback submission, get enhanced analysis
      const enhancedResponse = await fetch('http://localhost:5000/inference/enhanced', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          filename,
          scene_analysis: sceneContext 
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
    <div className="flex items-center justify-center min-h-screen bg-gray-900 text-white">
      <div className="max-w-4xl mx-auto p-8 text-center">
        <h1 className="text-3xl font-bold mb-8">
          Visual Reasoning with Few-Shot Learning
        </h1>

        {/* <div className="mb-6 flex justify-center gap-4">
          <button
            className={`px-4 py-2 rounded-md transition-colors ${
              mode === 'image' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
            }`}
            onClick={() => setMode('image')}
          >
            Image Analysis
          </button>
          <button
            className={`px-4 py-2 rounded-md transition-colors ${
              mode === 'text' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
            }`}
            onClick={() => setMode('text')}
          >
            Text Analysis
          </button>
        </div> */}
        
        {analysisStage === 'initial' && (
          <div className="mb-4">
            <div className="bg-gray-800 p-4 rounded-lg mb-4">
              <h3 className="text-lg font-semibold mb-2">Analyze Existing Image  from Images Folder</h3>
              <div className="flex items-center">
                <select
                  className="flex-grow p-2 bg-gray-700 rounded-l text-white"
                  value={filename}
                  onChange={handleFilenameChange}
                >
                  <option value="">Select an image...</option>
                  {existingFiles.map(file => (
                    <option key={file} value={file}>{file}</option>
                  ))}
                </select>
                <button
                  className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-r"
                  onClick={handleAnalyze}
                  disabled={loading || !filename}
                >
                  Analyze
                </button>
              </div>
            </div>

            <div 
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 mb-4 bg-gray-50 text-gray-800 transition-colors hover:border-blue-500"
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
            >
              {!imagePreview ? (
                <>
                  <h3 className="text-lg font-semibold mb-2">OR Upload New Image</h3>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageSelect}
                    id="file-input"
                    className="hidden"
                  />
                  <label 
                    htmlFor="file-input" 
                    className="cursor-pointer block w-full h-full"
                  >
                    <div className="flex flex-col items-center gap-4">
                      <i className="fas fa-cloud-upload-alt text-5xl"></i>
                      <p>Drag and drop an image or click to select</p>
                    </div>
                  </label>
                </>
              ) : (
                <div className="relative inline-block">
                  <ImagePreview file={selectedImage} />
                  <button 
                    className="absolute top-2 right-2 bg-white/90 px-4 py-2 rounded text-red-600 hover:bg-white"
                    onClick={resetState}
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {analysisStage === 'basic' && basicAnalysis && (
          <div className="mt-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Image Display */}
              <div className="bg-gray-800 p-6 rounded-lg shadow-sm">
                <h2 className="text-xl font-semibold mb-4">Selected Image</h2>
                <div className="flex justify-center items-center bg-[#1a1a1a] p-4 rounded-lg border border-gray-700 min-h-[300px]">
                  <img 
                    src={`http://localhost:5000/processed_images/${filename}`}
                    alt="Selected scene"
                    className="max-w-full max-h-[300px] object-contain"
                  />
                </div>
              </div>

              {/* Analysis Display */}
              <div className="bg-gray-800 p-6 rounded-lg shadow-sm">
                <h2 className="text-xl font-semibold mb-4">Basic Analysis</h2>
                <div className="bg-[#1a1a1a] p-6 rounded-lg border border-gray-700 min-h-[300px] text-left overflow-auto">
                  {typeof basicAnalysis === 'string' ? (
                    // Split the text into paragraphs and format them
                    basicAnalysis.split('\n').map((paragraph, index) => (
                      <p 
                        key={index} 
                        className={`text-gray-300 text-base leading-relaxed mb-4 ${
                          paragraph.startsWith('1.') || 
                          paragraph.startsWith('2.') || 
                          paragraph.startsWith('3.') 
                            ? 'font-semibold text-blue-400' 
                            : ''
                        }`}
                      >
                        {paragraph}
                      </p>
                    ))
                  ) : (
                    <pre className="whitespace-pre-wrap text-gray-300 text-base leading-relaxed">
                      {JSON.stringify(basicAnalysis, null, 2)}
                    </pre>
                  )}
                </div>
                <div className="mt-4">
                  <h3 className="text-lg font-semibold">Rate this analysis:</h3>
                  <StarRating rating={basicRating} setRating={setBasicRating} />
                  <textarea
                    className="w-full mt-2 p-2 bg-gray-700 text-white border border-gray-600 rounded resize-none"
                    placeholder="Optional feedback or comments..."
                    rows="2"
                    value={basicFeedback}
                    onChange={(e) => setBasicFeedback(e.target.value)}
                  ></textarea>
                  <button
                    className={`w-full mt-4 py-3 px-6 text-lg rounded-md transition-colors ${
                      submitting || basicRating === 0
                        ? 'bg-gray-400 cursor-not-allowed'
                        : 'bg-green-600 hover:bg-green-700 text-white'
                    }`}
                    onClick={handleFeedbackSubmit}
                    disabled={submitting || basicRating === 0}
                  >
                    {submitting ? 'Submitting...' : 'Submit Feedback & Get Enhanced Analysis'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {analysisStage === 'enhanced' && enhancedAnalysis && (
          <div className="mt-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Image Display */}
              <div className="bg-gray-800 p-6 rounded-lg shadow-sm">
                <h2 className="text-xl font-semibold mb-4">Selected Image</h2>
                <div className="flex justify-center items-center bg-[#1a1a1a] p-4 rounded-lg border border-gray-700 min-h-[300px]">
                  <img 
                    src={`http://localhost:5000/processed_images/${filename}`}
                    alt="Selected scene"
                    className="max-w-full max-h-[300px] object-contain"
                  />
                </div>
              </div>

              {/* Combined Analysis Display */}
              <div className="flex flex-col gap-6">
                {/* Basic Analysis */}
                <div className="bg-gray-800 p-6 rounded-lg shadow-sm">
                  <h2 className="text-xl font-semibold mb-4">Basic Analysis</h2>
                  <div className="bg-[#1a1a1a] p-6 rounded-lg border border-gray-700 min-h-[200px] text-left overflow-auto">
                    {typeof basicAnalysis === 'string' ? (
                      basicAnalysis.split('\n').map((paragraph, index) => (
                        <p 
                          key={index} 
                          className={`text-gray-300 text-base leading-relaxed mb-4 ${
                            paragraph.startsWith('1.') || 
                            paragraph.startsWith('2.') || 
                            paragraph.startsWith('3.') 
                              ? 'font-semibold text-blue-400' 
                              : ''
                          }`}
                        >
                          {paragraph}
                        </p>
                      ))
                    ) : (
                      <pre className="whitespace-pre-wrap text-gray-300 text-base leading-relaxed">
                        {JSON.stringify(basicAnalysis, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>

                {/* Enhanced Analysis */}
                <div className="bg-gray-800 p-6 rounded-lg shadow-sm">
                  <h2 className="text-xl font-semibold mb-4">Enhanced Analysis (Few-Shot Learning)</h2>
                  <div className="bg-[#1a1a1a] p-6 rounded-lg border border-gray-700 min-h-[200px] text-left overflow-auto">
                    {typeof enhancedAnalysis === 'string' ? (
                      enhancedAnalysis.split('\n').map((paragraph, index) => (
                        <p 
                          key={index} 
                          className={`text-gray-300 text-base leading-relaxed mb-4 ${
                            paragraph.startsWith('1.') || 
                            paragraph.startsWith('2.') || 
                            paragraph.startsWith('3.') 
                              ? 'font-semibold text-blue-400' 
                              : ''
                          }`}
                        >
                          {paragraph}
                        </p>
                      ))
                    ) : (
                      <pre className="whitespace-pre-wrap text-gray-300 text-base leading-relaxed">
                        {JSON.stringify(enhancedAnalysis, null, 2)}
                      </pre>
                    )}
                  </div>

                  {/* Add Relevant Patterns Section */}
                  {relevantPatterns && relevantPatterns.length > 0 && (
                    <div className="mt-6">
                      <h3 className="text-lg font-semibold mb-3 text-blue-400">
                        Patterns Used for Enhancement
                      </h3>
                      <div className="space-y-4">
                        {relevantPatterns.map((pattern, index) => (
                          <div key={index} className="bg-gray-700 p-4 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm text-gray-300">
                                Scene Type: {pattern.scene_type}
                              </span>
                              <span className="text-sm text-yellow-400">
                                Rating: {(pattern.rating * 5).toFixed(1)}/5
                              </span>
                            </div>
                            <p className="text-sm text-gray-200 mb-2">
                              {pattern.inference}
                            </p>
                            {pattern.typical_relationships?.length > 0 && (
                              <div className="text-xs text-gray-400">
                                <span className="font-semibold">Common patterns:</span>
                                {" " + pattern.typical_relationships.map(rel => 
                                  `${rel.subject} ${rel.spatial} ${rel.object}`
                                ).join(', ')}
                              </div>
                            )}
                            {pattern.atypical_relationships?.length > 0 && (
                              <div className="text-xs text-gray-400 mt-1">
                                <span className="font-semibold">Unusual patterns:</span>
                                {" " + pattern.atypical_relationships.map(rel => 
                                  `${rel.subject} ${rel.spatial} ${rel.object}`
                                ).join(', ')}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <button
              className="mt-8 bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-md transition-colors"
              onClick={resetState}
            >
              Analyze Another Image
            </button>
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 bg-red-100 text-red-700 rounded-md">
            {error}
          </div>
        )}

        {loading && (
          <div className="mt-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
            <p className="mt-2">Analyzing...</p>
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

export default ImageAnalysis;