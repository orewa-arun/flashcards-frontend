import React, { useState, useEffect, useRef } from 'react'
import ReactDOM from 'react-dom'
import { FaLightbulb, FaCalculator, FaSearchPlus, FaSearchMinus, FaExpandAlt } from 'react-icons/fa'
import * as d3 from 'd3'
import 'd3-graphviz'
import './LandingFlashcard.css'

const answerTypes = [
  { key: 'concise', label: 'Concise' },
  { key: 'analogy', label: 'Analogy' },
  { key: 'eli5', label: 'ELI5' },
  { key: 'real_world_use_case', label: 'Use Case' },
  { key: 'common_mistakes', label: 'Mistakes' },
  { key: 'example', label: 'Example' }
]

// Second Normal Form flashcard data
const flashcardData = {
  type: "concept",
  question: "Describe the purpose and characteristics of Second Normal Form (2NF) and how it builds upon First Normal Form.",
  answers: {
    concise: "Second Normal Form (2NF) eliminates partial dependencies, ensuring that all nonkey attributes are fully dependent on the entire primary key, not just part of it. A table must first be in 1NF before achieving 2NF. This applies specifically to tables with composite primary keys, where nonkey attributes must depend on the complete composite key rather than just one component of it.",
    analogy: "Think of 2NF like organizing a library checkout system. If you have a checkout record identified by both StudentID and BookID together, information about the student (like name) shouldn't be stored here because it only relates to StudentID, not the combination. Similarly, book information (like title) should be separate because it only relates to BookID. Only information about the checkout itself (like checkout date) belongs in the combined record.",
    eli5: "Imagine you have a notebook where you write down 'who borrowed which toy and when.' If you also write the person's phone number in that same line, that's silly because the phone number has nothing to do with which toy they borrowed—it's just about the person! 2NF means you should keep the phone numbers in a separate list just for people.",
    real_world_use_case: "Consider a sales database with a QUANTITY table using a composite primary key (SalespersonNumber, ProductNumber) that also stored SalespersonName and ProductName. To achieve 2NF, this table is split: the QUANTITY table keeps only the composite key and quantity sold (which depends on both salesperson AND product), while two new tables are created—SALESPERSON (with SalespersonNumber as PK and Name) and PRODUCT (with ProductNumber as PK and Name). This eliminates redundancy where salesperson names were repeated for every product they sold.",
    common_mistakes: "A common mistake is thinking 2NF applies to all tables. It only matters for tables with composite primary keys. Another mistake is removing attributes that actually DO depend on the entire composite key. For example, in an order line item with OrderID and ProductID as the composite key, the quantity ordered correctly depends on both—it's specific to that product in that particular order—so it should stay. Only attributes depending on just part of the key need to be moved."
  },
  example: "In an e-commerce system, an ORDER_ITEMS table initially uses (OrderID, ProductID) as a composite primary key and includes columns: Quantity, OrderDate, CustomerName, ProductPrice, and ProductCategory. To achieve 2NF: (1) Keep Quantity in ORDER_ITEMS since it depends on both OrderID and ProductID; (2) Move OrderDate and CustomerName to an ORDERS table (they depend only on OrderID); (3) Move ProductPrice and ProductCategory to a PRODUCTS table (they depend only on ProductID). This eliminates the redundancy where product information was repeated for every order line, and order information was repeated for every product in that order.",
  mermaid_diagrams: {
    concise: `graph TD
    subgraph Before 2NF
        Table1[Table with<br/>Composite PK<br/>+ Partial Dependencies]
    end
    subgraph After 2NF
        Table2[Main Table:<br/>Composite PK<br/>+ Full Dependencies]
        Table3[New Table 1:<br/>Part of PK<br/>+ Its Attributes]
        Table4[New Table 2:<br/>Other Part of PK<br/>+ Its Attributes]
    end
    Table1 -->|Split| Table2
    Table1 -->|Extract| Table3
    Table1 -->|Extract| Table4
    style Table2 fill:#ccffcc
    style Table3 fill:#cce5ff
    style Table4 fill:#ffe5cc`,
    analogy: `graph TD
    Before[Checkout Record:<br/>StudentID + BookID<br/>Student Name<br/>Book Title<br/>Checkout Date]
    After1[Checkout:<br/>StudentID + BookID<br/>Checkout Date]
    After2[Students:<br/>StudentID<br/>Student Name]
    After3[Books:<br/>BookID<br/>Book Title]
    Before -->|2NF Split| After1
    Before -->|Extract Student Info| After2
    Before -->|Extract Book Info| After3
    After1 -.->|References| After2
    After1 -.->|References| After3
    style After1 fill:#ccffcc
    style After2 fill:#cce5ff
    style After3 fill:#ffe5cc`,
    eli5: `graph TD
    Wrong[Notebook with<br/>Toy + Person + Phone]
    Right1[Toy Borrowing<br/>List]
    Right2[Person Phone<br/>List]
    Wrong -->|Separate!| Right1
    Wrong -->|Move phones here!| Right2
    Right1 -.->|Look up person| Right2
    style Wrong fill:#ffcccc
    style Right1 fill:#ccffcc
    style Right2 fill:#cce5ff`,
    real_world_use_case: `graph TD
    Before[QUANTITY Table<br/>SalespersonNum + ProductNum<br/>Quantity<br/>SalespersonName<br/>ProductName]
    After1[QUANTITY<br/>SalespersonNum + ProductNum<br/>Quantity]
    After2[SALESPERSON<br/>SalespersonNum<br/>Name]
    After3[PRODUCT<br/>ProductNum<br/>Name]
    Before -->|Split| After1
    Before -->|Extract| After2
    Before -->|Extract| After3
    After1 -.->|FK| After2
    After1 -.->|FK| After3
    style Before fill:#ffcccc
    style After1 fill:#ccffcc
    style After2 fill:#cce5ff
    style After3 fill:#ffe5cc`,
    common_mistakes: `graph LR
    M1[Mistake:<br/>Apply 2NF to<br/>single-key tables]
    M2[Mistake:<br/>Remove attributes<br/>that depend on<br/>full composite key]
    C1[Correct:<br/>2NF only for<br/>composite keys]
    C2[Correct:<br/>Keep full<br/>dependencies]
    M1 -.->|Learn| C1
    M2 -.->|Understand| C2
    style M1 fill:#ffcccc
    style M2 fill:#ffcccc
    style C1 fill:#ccffcc
    style C2 fill:#ccffcc`,
    example: `graph TD
    Before[ORDER_ITEMS<br/>OrderID + ProductID<br/>Quantity, OrderDate<br/>CustomerName, ProductPrice<br/>ProductCategory]
    After1[ORDER_ITEMS<br/>OrderID + ProductID<br/>Quantity]
    After2[ORDERS<br/>OrderID<br/>OrderDate<br/>CustomerName]
    After3[PRODUCTS<br/>ProductID<br/>ProductPrice<br/>ProductCategory]
    Before -->|Keep Quantity| After1
    Before -->|Move Order data| After2
    Before -->|Move Product data| After3
    After1 -.->|FK| After2
    After1 -.->|FK| After3
    style Before fill:#ffcccc
    style After1 fill:#ccffcc
    style After2 fill:#cce5ff
    style After3 fill:#ffe5cc`
  },
  math_visualizations: {
    concise: `/* layout=dot */
digraph SecondNormalForm {
    rankdir=TB;
    node [shape=box, margin=0.3, fontsize=11, style=filled];
    
    Before [label="Table with Composite PK\\n(A, B) + Attributes\\nC depends on A only\\nD depends on B only\\nE depends on (A,B)", fillcolor="#ffcccc"];
    
    After1 [label="Main Table\\n(A, B) -> E", fillcolor="#ccffcc"];
    After2 [label="Table 1\\nA -> C", fillcolor="#cce5ff"];
    After3 [label="Table 2\\nB -> D", fillcolor="#ffe5cc"];
    
    Before -> After1 [label="Keep full\\ndependencies"];
    Before -> After2 [label="Extract partial\\ndependency on A"];
    Before -> After3 [label="Extract partial\\ndependency on B"];
    
    label="Second Normal Form Decomposition";
    labelloc="t";
    fontsize=14;
}`,
    analogy: `/* layout=dot */
digraph LibraryCheckout {
    rankdir=LR;
    node [shape=record, margin=0.3, fontsize=10, style=filled];
    
    subgraph cluster_before {
        label="Before 2NF: Mixed Data";
        style=filled;
        fillcolor="#fff0f0";
        Before [label="<pk>StudentID + BookID|Student Name|Book Title|Checkout Date", fillcolor="#ffcccc"];
    }
    
    subgraph cluster_after {
        label="After 2NF: Separated Tables";
        style=filled;
        fillcolor="#f0fff0";
        Checkout [label="<pk>StudentID + BookID|Checkout Date", fillcolor="#ccffcc"];
        Students [label="<pk>StudentID|Student Name", fillcolor="#cce5ff"];
        Books [label="<pk>BookID|Book Title", fillcolor="#ffe5cc"];
    }
    
    Before -> Checkout [label="2NF\\nTransform"];
    Checkout -> Students [label="FK", style=dashed];
    Checkout -> Books [label="FK", style=dashed];
}`,
    eli5: `/* layout=dot */
digraph ToyBox {
    rankdir=TB;
    node [shape=ellipse, margin=0.3, fontsize=11, style=filled];
    
    Wrong [label="❌ Wrong Way\\nToy + Person\\nwith Phone Number", fillcolor="#ffcccc", shape=box];
    
    Right1 [label="✓ Toy + Person\\nRecord", fillcolor="#ccffcc", shape=box];
    Right2 [label="✓ Person List\\nwith Phone Numbers", fillcolor="#cce5ff", shape=box];
    
    Wrong -> Right1 [label="Separate!"];
    Wrong -> Right2 [label="Move phone\\nnumbers here"];
    
    label="Keep Related Things Together";
    labelloc="t";
    fontsize=13;
}`,
    real_world_use_case: `/* layout=dot */
digraph SalesDatabase {
    rankdir=TB;
    node [shape=record, margin=0.3, fontsize=10, style=filled];
    
    subgraph cluster_before {
        label="Before 2NF: QUANTITY Table";
        style=filled;
        fillcolor="#fff0f0";
        QtyBefore [label="<pk>SalespersonNum + ProductNum|Quantity|SalespersonName|ProductName", fillcolor="#ffcccc"];
    }
    
    subgraph cluster_after {
        label="After 2NF: Three Tables";
        style=filled;
        fillcolor="#f0fff0";
        QtyAfter [label="<pk>SalespersonNum + ProductNum|Quantity", fillcolor="#ccffcc"];
        Salesperson [label="<pk>SalespersonNum|Name", fillcolor="#cce5ff"];
        Product [label="<pk>ProductNum|Name", fillcolor="#ffe5cc"];
    }
    
    QtyBefore -> QtyAfter [label="Keep only\\nfull dependencies"];
    QtyBefore -> Salesperson [label="Extract\\nSalesperson data"];
    QtyBefore -> Product [label="Extract\\nProduct data"];
    
    QtyAfter -> Salesperson [label="FK", style=dashed];
    QtyAfter -> Product [label="FK", style=dashed];
}`,
    common_mistakes: `/* layout=dot */
digraph CommonMistakes {
    rankdir=LR;
    node [shape=box, margin=0.3, fontsize=10, style=filled];
    
    subgraph cluster_mistake {
        label="❌ Common Mistake";
        style=filled;
        fillcolor="#fff0f0";
        M1 [label="Applying 2NF to\\nsingle-key tables", fillcolor="#ffcccc"];
        M2 [label="Removing attributes\\nthat depend on\\nfull composite key", fillcolor="#ffcccc"];
    }
    
    subgraph cluster_correct {
        label="✓ Correct Understanding";
        style=filled;
        fillcolor="#f0fff0";
        C1 [label="2NF only applies to\\ncomposite keys", fillcolor="#ccffcc"];
        C2 [label="Keep attributes that\\ndepend on entire\\ncomposite key", fillcolor="#ccffcc"];
    }
    
    M1 -> C1 [label="Learn"];
    M2 -> C2 [label="Understand"];
}`,
    example: `/* layout=dot */
digraph EcommerceExample {
    rankdir=TB;
    node [shape=record, margin=0.3, fontsize=10, style=filled];
    
    subgraph cluster_before {
        label="Before 2NF: ORDER_ITEMS";
        style=filled;
        fillcolor="#fff0f0";
        OIBefore [label="<pk>OrderID + ProductID|Quantity|OrderDate|CustomerName|ProductPrice|ProductCategory", fillcolor="#ffcccc"];
    }
    
    subgraph cluster_after {
        label="After 2NF: Normalized Tables";
        style=filled;
        fillcolor="#f0fff0";
        OIAfter [label="<pk>OrderID + ProductID|Quantity", fillcolor="#ccffcc"];
        Orders [label="<pk>OrderID|OrderDate|CustomerName", fillcolor="#cce5ff"];
        Products [label="<pk>ProductID|ProductPrice|ProductCategory", fillcolor="#ffe5cc"];
    }
    
    OIBefore -> OIAfter [label="(1) Keep Quantity\\ndepends on both"];
    OIBefore -> Orders [label="(2) Move Order\\ndata"];
    OIBefore -> Products [label="(3) Move Product\\ndata"];
    
    OIAfter -> Orders [label="FK", style=dashed];
    OIAfter -> Products [label="FK", style=dashed];
}`
  }
}

function escapeHtml(str = '') {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function LandingFlashcard() {
  const [isFlipped, setIsFlipped] = useState(false)
  const [selectedAnswer, setSelectedAnswer] = useState('concise')
  const [showMathLarge, setShowMathLarge] = useState(false)
  const [graphvizLoading, setGraphvizLoading] = useState(false)
  const [graphvizError, setGraphvizError] = useState(null)
  const graphvizRef = useRef(null)
  const graphvizInstanceRef = useRef(null)

  const handleCardClick = (e) => {
    // Check if click is on any interactive element
    if (e.target.closest('.answer-selector') ||
        e.target.closest('.answer-type-btn') ||
        e.target.closest('.math-viz-section') ||
        e.target.closest('.math-lookup-btn')) {
      return
    }
    setIsFlipped(!isFlipped)
  }

  // Graphviz render effect for math diagrams
  useEffect(() => {
    if (!showMathLarge || !flashcardData.math_visualizations?.[selectedAnswer]?.trim()) {
      return
    }

    const dotCode = flashcardData.math_visualizations[selectedAnswer].trim()
    if (!dotCode) return

    let mounted = true

    const renderGraphviz = async () => {
      if (!graphvizRef.current) return

      try {
        setGraphvizLoading(true)
        setGraphvizError(null)

        // Clear previous content
        d3.select(graphvizRef.current).selectAll('*').remove()

        // Render the DOT code with enhanced settings
        const graphvizInstance = d3.select(graphvizRef.current)
          .graphviz({
            fit: true,
            zoom: true,
            transition: (selection) => {
              return selection.transition().duration(300)
            }
          })
          .on('renderEnd', () => {
            // Apply custom styling to the rendered SVG
            const svg = d3.select(graphvizRef.current).select('svg')
            if (svg.node()) {
              svg.selectAll('text')
                .style('font-family', 'system-ui, -apple-system, sans-serif')
                .style('font-weight', '500')

              svg.selectAll('path')
                .style('stroke-width', '2')
                .style('fill', 'none')

              svg.selectAll('.node')
                .style('stroke-width', '1.5')

              svg.selectAll('.cluster rect')
                .style('fill-opacity', '0.06')
                .style('stroke-dasharray', '6,3')

              svg.selectAll('.cluster text')
                .style('font-weight', '600')
                .style('font-size', '12px')
            }
          })

        graphvizInstanceRef.current = graphvizInstance

        await graphvizInstance.renderDot(dotCode)

        if (mounted) {
          setGraphvizLoading(false)
        }
      } catch (err) {
        console.error('Graphviz rendering error:', err)
        if (mounted) {
          setGraphvizError(err.message || 'Failed to render mathematical diagram')
          setGraphvizLoading(false)
        }
      }
    }

    renderGraphviz()

    return () => {
      mounted = false
    }
  }, [showMathLarge, selectedAnswer])

  const handleZoomIn = () => {
    if (graphvizInstanceRef.current) {
      const svg = d3.select(graphvizRef.current).select('svg')
      graphvizInstanceRef.current.zoomBehavior().scaleBy(svg.transition().duration(250), 1.2)
    }
  }

  const handleZoomOut = () => {
    if (graphvizInstanceRef.current) {
      const svg = d3.select(graphvizRef.current).select('svg')
      graphvizInstanceRef.current.zoomBehavior().scaleBy(svg.transition().duration(250), 1 / 1.2)
    }
  }

  const handleZoomReset = () => {
    if (graphvizInstanceRef.current) {
      graphvizInstanceRef.current.resetZoom(d3.transition().duration(500))
    }
  }

  const getAnswerContent = () => {
    if (selectedAnswer === 'example') return flashcardData.example || 'No example available.'
    return flashcardData.answers?.[selectedAnswer] || 'No answer available.'
  }

  return (
    <div className="landing-flashcard-wrapper">
      <div 
        className={`landing-flashcard ${isFlipped ? 'flipped' : ''}`}
        onClick={handleCardClick}
      >
        <div className="landing-flashcard-front">
          <div className="card-content">
            <div className="question-icon">
              <FaLightbulb />
            </div>
            <div className="question-text">{flashcardData.question}</div>
            <div className="flip-hint">Click to reveal answer</div>
          </div>
        </div>
        
        <div className="landing-flashcard-back">
          <div className="card-content">
            <div className="answer-selector" onClick={(e) => e.stopPropagation()}>
              {answerTypes.map((type, idx) => (
                <button
                  key={type.key}
                  className={`answer-type-btn ${selectedAnswer === type.key ? 'active' : ''}`}
                  onClick={(e) => { 
                    e.preventDefault(); 
                    e.stopPropagation(); 
                    setSelectedAnswer(type.key);
                  }}
                  title={`${type.label} (${idx + 1})`}
                >
                  <span className="shortcut-key">{idx + 1}</span>
                  <span className="tab-label">{type.label}</span>
                </button>
              ))}
            </div>
            
            <div className="answer-content">
              <div className="answer-text">{getAnswerContent()}</div>
              
              {flashcardData.mermaid_diagrams?.[selectedAnswer]?.trim() && (
                <div className="mermaid-diagram-wrapper">
                  <div className="mermaid-diagram-container">
                    <img 
                      src={`/demo_diagrams/mermaid_${selectedAnswer}.png`} 
                      alt={`${selectedAnswer} diagram`}
                      className="mermaid-diagram-image"
                      onError={(e) => {
                        e.target.style.display = 'none'
                        console.error('Failed to load diagram image')
                      }}
                    />
                  </div>
                </div>
              )}
              
              {/* Math Visualization Button */}
              {flashcardData.math_visualizations?.[selectedAnswer]?.trim() && (
                <div className="math-viz-section">
                  <button
                    className="math-lookup-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowMathLarge(true);
                    }}
                    title="View mathematical diagram"
                  >
                    <FaCalculator /> View Math Diagram
                  </button>
                </div>
              )}

              {/* Large Modal for Mathematical Diagrams */}
              {showMathLarge && ReactDOM.createPortal(
                <>
                  <div className="math-modal-large-backdrop" onClick={() => setShowMathLarge(false)}></div>
                  <div className="math-modal-large" onClick={(e) => e.stopPropagation()}>
                    <div className="math-modal-large-content" onClick={(e) => e.stopPropagation()}>
                      <button className="math-close-btn" onClick={() => setShowMathLarge(false)}>×</button>
                      <div className="math-modal-header">
                        <h3>🔢 Math Diagram</h3>
                        <p>For {selectedAnswer.replace(/_/g, ' ')}</p>
                      </div>

                      {/* Graphviz Rendering Container */}
                      <div className="math-diagram-container-large">
                        {graphvizLoading && (
                          <div className="graphviz-loading">
                            <div className="graphviz-spinner"></div>
                            <p>Rendering mathematical diagram...</p>
                          </div>
                        )}
                        {graphvizError && (
                          <div className="graphviz-error">
                            <p>⚠️ Failed to render diagram: {graphvizError}</p>
                          </div>
                        )}
                        <div
                          ref={graphvizRef}
                          className="graphviz-diagram-large"
                        ></div>

                        <div className="math-modal-controls">
                          <button onClick={handleZoomIn} className="math-zoom-btn" title="Zoom In"><FaSearchPlus /></button>
                          <button onClick={handleZoomOut} className="math-zoom-btn" title="Zoom Out"><FaSearchMinus /></button>
                          <button onClick={handleZoomReset} className="math-zoom-btn" title="Reset Zoom"><FaExpandAlt /></button>
                        </div>
                      </div>

                      {/* Always show the source code */}
                      <details className="math-code-details">
                        <summary>View Graphviz DOT Code</summary>
                        <pre><code>{flashcardData.math_visualizations[selectedAnswer]}</code></pre>
                      </details>
                    </div>
                  </div>
                </>,
                document.getElementById('modal-root')
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LandingFlashcard
