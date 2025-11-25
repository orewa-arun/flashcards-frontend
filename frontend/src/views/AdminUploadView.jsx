import { useState } from 'react'
import { FaCloudUploadAlt, FaCog } from 'react-icons/fa'
import { IngestionForm, LecturePipelineList } from '../components/ContentPipeline'
import './AdminUploadView.css'

function AdminUploadView() {
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handleIngestionComplete = () => {
    // Trigger a refresh of the lecture list
    setRefreshTrigger(prev => prev + 1)
  }

  return (
    <div className="admin-upload-view">
      <div className="admin-upload-header">
        <h1>
          <FaCloudUploadAlt className="title-icon" />
          Content Pipeline Manager
        </h1>
        <p className="header-subtitle">
          Upload lecture PDFs and manage the automated content processing pipeline
        </p>
      </div>

      <div className="admin-upload-content">
        <IngestionForm onIngestionComplete={handleIngestionComplete} />
        <LecturePipelineList refreshTrigger={refreshTrigger} />
      </div>

      <div className="admin-upload-footer">
        <div className="pipeline-info">
          <FaCog className="info-icon" />
          <div className="info-text">
            <strong>Pipeline Stages:</strong>
            <span>Analysis → Flashcards → Quiz → Indexing</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AdminUploadView

