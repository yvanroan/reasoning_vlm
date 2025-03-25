import React, { useState, useEffect } from 'react';
import './ImageAnalysis.css';

const ImageAnalysis = () => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [textInput, setTextInput] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('image'); // 'image' or 'text'

  const handleImageSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
      setImagePreview(URL.createObjectURL(file));
      setAnalysis(null);
      setError(null);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedImage(file);
      setImagePreview(URL.createObjectURL(file));
      setAnalysis(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedImage) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('image', selectedImage);

    try {
      const response = await fetch('http://localhost:5000/analyze/relationships/image', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError('Failed to analyze image. Please try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTextAnalyze = async () => {
    if (!textInput.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:5000/analyze/text', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: textInput }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError('Failed to analyze text. Please try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const resetState = () => {
    setSelectedImage(null);
    setImagePreview(null);
    setTextInput('');
    setAnalysis(null);
    setError(null);
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900 text-white">
      <div className="max-w-3xl mx-auto p-8 text-center">
        <h1 className="text-3xl font-bold mb-8">
          AI Analysis with Gemini
        </h1>

        <div className="mb-6 flex justify-center gap-4">
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
        </div>
        
        {mode === 'image' ? (
          <div 
            className="border-2 border-dashed border-gray-300 rounded-lg p-8 mb-4 bg-gray-50 text-gray-800 transition-colors hover:border-blue-500"
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
          >
            {!imagePreview ? (
              <>
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
        ) : (
          <div className="mb-4">
            <textarea
              className="w-full h-32 p-4 bg-gray-800 text-white border border-gray-700 rounded-lg resize-none"
              placeholder="Enter your text here..."
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
            />
          </div>
        )}

        {mode === 'image' && selectedImage && !analysis && (
          <button 
            className={`w-full py-3 px-6 text-lg rounded-md transition-colors ${
              loading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? 'Analyzing...' : 'Analyze Image'}
          </button>
        )}

        {mode === 'text' && textInput && !analysis && (
          <button 
            className={`w-full py-3 px-6 text-lg rounded-md transition-colors ${
              loading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
            onClick={handleTextAnalyze}
            disabled={loading}
          >
            {loading ? 'Analyzing...' : 'Analyze Text'}
          </button>
        )}

        {error && (
          <div className="mt-4 p-4 bg-red-100 text-red-700 rounded-md">
            {error}
          </div>
        )}

        {analysis && (
          <div className="mt-8 bg-gray-800 p-6 rounded-lg shadow-sm">
            <h2 className="text-2xl font-semibold mb-4">Analysis Results</h2>
            <div className="bg-[#1a1a1a] p-6 rounded-lg border border-gray-700">
              <p className="text-gray-200 text-center whitespace-pre-wrap">
                {typeof analysis === 'string' ? analysis : JSON.stringify(analysis, null, 2)}
              </p>
            </div>
            <div className="mt-6">
              <button 
                className="bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-md transition-colors"
                onClick={resetState}
              >
                Start New Analysis
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

export default ImageAnalysis;