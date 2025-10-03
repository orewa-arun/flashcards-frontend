import './DifficultyRating.css'

function DifficultyRating({ onRate }) {
  return (
    <div className="difficulty-rating">
      <h3>How well did you recall this concept?</h3>
      <div className="rating-buttons">
        <button 
          className="rating-btn easy"
          onClick={() => onRate('easy')}
        >
          😊 Easy
        </button>
        <button 
          className="rating-btn okay"
          onClick={() => onRate('okay')}
        >
          🤔 Okay
        </button>
        <button 
          className="rating-btn hard"
          onClick={() => onRate('hard')}
        >
          😓 Hard
        </button>
      </div>
    </div>
  )
}

export default DifficultyRating

