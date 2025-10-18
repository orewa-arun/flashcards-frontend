/**
 * Weighted random sampling - picks flashcards based on relevance scores
 * Higher scored cards are more likely to be selected
 */
export function selectQuizFlashcards(flashcards, count = 10) {
  if (!flashcards || flashcards.length === 0) return []
  
  // If we have fewer flashcards than requested, return all
  if (flashcards.length <= count) return [...flashcards]
  
  // Create a weighted pool based on relevance scores
  const weightedPool = []
  flashcards.forEach((card, index) => {
    const weight = card.relevance_score?.score || 5 // default weight of 5 if no score
    // Add this card to the pool 'weight' times
    for (let i = 0; i < weight; i++) {
      weightedPool.push(index)
    }
  })
  
  // Shuffle the weighted pool
  const shuffled = shuffleArray(weightedPool)
  
  // Pick unique flashcard indices
  const selectedIndices = new Set()
  for (const index of shuffled) {
    selectedIndices.add(index)
    if (selectedIndices.size >= count) break
  }
  
  // Return the selected flashcards
  return Array.from(selectedIndices).map(i => flashcards[i])
}

/**
 * Select one random recall question from each flashcard
 */
export function selectRandomRecallQuestions(flashcards) {
  return flashcards.map(card => {
    if (!card.recall_questions || card.recall_questions.length === 0) {
      return null
    }
    
    const randomIndex = Math.floor(Math.random() * card.recall_questions.length)
    return {
      ...card.recall_questions[randomIndex],
      flashcardId: card.question, // For reference
      flashcardContext: card.context
    }
  }).filter(q => q !== null)
}

/**
 * Shuffle an array using Fisher-Yates algorithm
 */
function shuffleArray(array) {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

/**
 * Check if a user's answer is correct for different question types
 */
export function checkAnswer(question, userAnswer) {
  switch (question.type) {
    case 'mcq':
    case 'scenario_mcq':
      return userAnswer === question.answer
    
    case 'sequencing':
      // Check if arrays match exactly
      if (!Array.isArray(userAnswer) || !Array.isArray(question.answer)) return false
      if (userAnswer.length !== question.answer.length) return false
      return userAnswer.every((item, index) => item === question.answer[index])
    
    case 'categorization':
      // Check if categorization matches
      if (typeof userAnswer !== 'object' || typeof question.answer !== 'object') return false
      const userKeys = Object.keys(userAnswer).sort()
      const correctKeys = Object.keys(question.answer).sort()
      if (userKeys.length !== correctKeys.length) return false
      if (!userKeys.every((key, i) => key === correctKeys[i])) return false
      
      // Check each category's items
      return userKeys.every(key => {
        const userItems = (userAnswer[key] || []).sort()
        const correctItems = (question.answer[key] || []).sort()
        if (userItems.length !== correctItems.length) return false
        return userItems.every((item, i) => item === correctItems[i])
      })
    
    case 'matching':
      // Check if matching pairs are correct
      if (!Array.isArray(userAnswer) || !Array.isArray(question.answer)) return false
      if (userAnswer.length !== question.answer.length) return false
      const sortedUser = [...userAnswer].sort()
      const sortedCorrect = [...question.answer].sort()
      return sortedUser.every((pair, index) => pair === sortedCorrect[index])
    
    case 'fill_in_the_blank':
      // Case-insensitive comparison, trimming whitespace
      if (!userAnswer) return false
      return userAnswer.trim().toLowerCase() === question.answer.trim().toLowerCase()
    
    case 'true_false':
      // Direct string comparison for True/False
      return userAnswer === question.answer
    
    default:
      return false
  }
}

/**
 * Calculate quiz score
 */
export function calculateScore(results) {
  if (!results || results.length === 0) return 0
  const correct = results.filter(r => r.isCorrect).length
  return Math.round((correct / results.length) * 100)
}

