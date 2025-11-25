import { useState } from 'react'
import { FaUpload, FaSpinner, FaCheckCircle, FaBook, FaUser, FaCode, FaInfoCircle } from 'react-icons/fa'
import { contentPipeline } from '../../api/contentPipeline'
import './IngestionForm.css'

function IngestionForm({ onIngestionComplete }) {
  const [formData, setFormData] = useState({
    course_code: '',
    course_name: '',
    instructor: '',
    reference_textbooks: '',
    additional_info: ''
  })
  const [pdfFiles, setPdfFiles] = useState([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files)
    setPdfFiles(files)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    if (!formData.course_code || !formData.course_name) {
      setError('Course code and name are required')
      return
    }

    if (pdfFiles.length === 0) {
      setError('Please select at least one PDF file')
      return
    }

    setIsSubmitting(true)

    try {
      const submitData = new FormData()
      
      // Add form fields
      submitData.append('course_code', formData.course_code)
      submitData.append('course_name', formData.course_name)
      submitData.append('instructor', formData.instructor)
      submitData.append('additional_info', formData.additional_info)
      
      // Parse reference textbooks as JSON array
      if (formData.reference_textbooks) {
        const textbooks = formData.reference_textbooks
          .split(',')
          .map(t => t.trim())
          .filter(t => t.length > 0)
        submitData.append('reference_textbooks', JSON.stringify(textbooks))
      }

      // Add PDF files
      pdfFiles.forEach((file) => {
        submitData.append('pdf_files', file)
      })

      console.log('Submitting ingestion request...', {
        course_code: formData.course_code,
        course_name: formData.course_name,
        files: pdfFiles.map(f => f.name)
      })

      const response = await contentPipeline.ingestContent(submitData)
      
      console.log('Ingestion response:', response)
      
      setSuccess(`Successfully ingested ${pdfFiles.length} lecture(s) for course "${formData.course_name}"`)
      
      // Reset form
      setFormData({
        course_code: '',
        course_name: '',
        instructor: '',
        reference_textbooks: '',
        additional_info: ''
      })
      setPdfFiles([])
      
      // Reset file input
      const fileInput = document.getElementById('pdf_files')
      if (fileInput) fileInput.value = ''
      
      // Notify parent to refresh lecture list
      if (onIngestionComplete) {
        onIngestionComplete(response)
      }
    } catch (err) {
      console.error('Ingestion error:', err)
      setError(err.message || 'Failed to ingest content')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="ingestion-form-container">
      <div className="form-header">
        <h2>
          <FaUpload className="header-icon" />
          Upload Course Content
        </h2>
        <p className="form-description">
          Upload lecture PDFs to begin the content processing pipeline
        </p>
      </div>

      <form onSubmit={handleSubmit} className="ingestion-form">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="course_code">
              <FaCode className="label-icon" />
              Course Code <span className="required">*</span>
            </label>
            <input
              type="text"
              id="course_code"
              name="course_code"
              value={formData.course_code}
              onChange={handleInputChange}
              placeholder="e.g., MAPP_F_MKT404_EN_2025"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="course_name">
              <FaBook className="label-icon" />
              Course Name <span className="required">*</span>
            </label>
            <input
              type="text"
              id="course_name"
              name="course_name"
              value={formData.course_name}
              onChange={handleInputChange}
              placeholder="e.g., Marketing Analytics"
              required
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="instructor">
              <FaUser className="label-icon" />
              Instructor
            </label>
            <input
              type="text"
              id="instructor"
              name="instructor"
              value={formData.instructor}
              onChange={handleInputChange}
              placeholder="e.g., Dr. John Smith"
            />
          </div>

          <div className="form-group">
            <label htmlFor="reference_textbooks">
              <FaBook className="label-icon" />
              Reference Textbooks
            </label>
            <input
              type="text"
              id="reference_textbooks"
              name="reference_textbooks"
              value={formData.reference_textbooks}
              onChange={handleInputChange}
              placeholder="Comma-separated, e.g., Book 1, Book 2"
            />
          </div>
        </div>

        <div className="form-group full-width">
          <label htmlFor="additional_info">
            <FaInfoCircle className="label-icon" />
            Additional Information
          </label>
          <textarea
            id="additional_info"
            name="additional_info"
            value={formData.additional_info}
            onChange={handleInputChange}
            placeholder="Any additional course information or notes..."
            rows={3}
          />
        </div>

        <div className="form-group full-width">
          <label htmlFor="pdf_files">
            <FaUpload className="label-icon" />
            Lecture PDFs <span className="required">*</span>
          </label>
          <div className="file-input-container">
            <input
              type="file"
              id="pdf_files"
              name="pdf_files"
              accept=".pdf"
              multiple
              onChange={handleFileChange}
              className="file-input"
            />
            <div className="file-input-display">
              {pdfFiles.length > 0 ? (
                <div className="selected-files">
                  <span className="file-count">{pdfFiles.length} file(s) selected</span>
                  <ul className="file-list">
                    {pdfFiles.map((file, index) => (
                      <li key={index}>{file.name}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <span className="placeholder">Click to select PDF files or drag and drop</span>
              )}
            </div>
          </div>
        </div>

        {error && (
          <div className="form-message error">
            {error}
          </div>
        )}

        {success && (
          <div className="form-message success">
            <FaCheckCircle className="message-icon" />
            {success}
          </div>
        )}

        <button 
          type="submit" 
          className="submit-btn"
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <FaSpinner className="spinner" />
              Uploading...
            </>
          ) : (
            <>
              <FaUpload />
              Upload & Ingest
            </>
          )}
        </button>
      </form>
    </div>
  )
}

export default IngestionForm
