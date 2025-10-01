"""
LaTeX Configuration and Templates
All LaTeX-related settings and template generation
"""

from typing import Dict, Any


class LaTeXConfig:
    """LaTeX document configuration."""
    
    # Document class and basic settings
    DOCUMENT_CLASS = "article"
    DOCUMENT_OPTIONS = "a4paper,12pt"
    
    # Page margins
    PAGE_MARGIN = "1in"
    
    # Color definitions (RGB)
    COLORS = {
        'questionbg': (240, 248, 255),  # Alice Blue
        'answerbg': (255, 250, 240),    # Floral White
        'formulabg': (240, 255, 240),   # Honeydew
    }
    
    # Required LaTeX packages
    PACKAGES = [
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage{amsmath}",
        r"\usepackage{amssymb}",
        r"\usepackage{amsthm}",
        r"\usepackage{enumitem}",
        r"\usepackage{xcolor}",
        r"\usepackage{mdframed}",
        r"\usepackage{tcolorbox}",
        r"\usepackage{fancyhdr}",
    ]
    
    # Flashcard box settings
    FLASHCARD_BOX = {
        'border_radius': '2mm',
        'border_color': 'black!20',
        'top_padding': '5mm',
        'bottom_padding': '5mm',
    }


class LaTeXTemplates:
    """LaTeX document templates and generators."""
    
    @staticmethod
    def get_document_header(title: str) -> str:
        """Generate LaTeX document header."""
        packages_str = "\n".join(LaTeXConfig.PACKAGES)
        
        # Color definitions
        colors_str = "\n".join([
            f"\\definecolor{{{name}}}{{RGB}}{{{r},{g},{b}}}"
            for name, (r, g, b) in LaTeXConfig.COLORS.items()
        ])
        
        return rf"""\documentclass[{LaTeXConfig.DOCUMENT_OPTIONS}]{{{LaTeXConfig.DOCUMENT_CLASS}}}
{packages_str}

% Custom colors
{colors_str}

% Flashcard environment
\tcbuselibrary{{skins,breakable}}

\newtcolorbox{{flashcard}}[2][]{{
  enhanced,
  breakable,
  colback=#2,
  colframe={LaTeXConfig.FLASHCARD_BOX['border_color']},
  arc={LaTeXConfig.FLASHCARD_BOX['border_radius']},
  title=#1,
  fonttitle=\bfseries,
  top={LaTeXConfig.FLASHCARD_BOX['top_padding']},
  bottom={LaTeXConfig.FLASHCARD_BOX['bottom_padding']},
}}

\pagestyle{{fancy}}
\fancyhf{{}}
\rhead{{{title}}}
\lhead{{Study Material}}
\rfoot{{Page \thepage}}

\title{{{title}}}
\author{{AI-Generated Flashcards}}
\date{{\today}}

\begin{{document}}

\maketitle

"""
    
    @staticmethod
    def get_course_info_section(analysis: Dict[str, Any], total_flashcards: int) -> str:
        """Generate course information section."""
        topics = ', '.join(analysis.get('topics', []))
        difficulty = analysis.get('difficulty_level', 'Intermediate').title()
        
        return rf"""\section*{{Course Information}}
\begin{{itemize}}
    \item \textbf{{Topics:}} {topics}
    \item \textbf{{Difficulty:}} {difficulty}
    \item \textbf{{Total Flashcards:}} {total_flashcards}
\end{{itemize}}

\newpage

\section*{{Flashcards}}

"""
    
    @staticmethod
    def get_flashcard_card(
        card_num: int,
        card_type: str,
        difficulty: str,
        question: str,
        answer: str,
        tags: str
    ) -> str:
        """Generate a single flashcard."""
        # Choose background color based on type
        bg_color = 'formulabg' if card_type == 'Formula' else 'questionbg'
        
        return rf"""\subsection*{{Card {card_num}: {card_type} (\textit{{{difficulty}}})}}

\begin{{flashcard}}[Question]{{{bg_color}}}
{question}
\end{{flashcard}}

\vspace{{5mm}}

\begin{{flashcard}}[Answer]{{answerbg}}
{answer}

\vspace{{3mm}}
\textit{{Tags: {tags}}}
\end{{flashcard}}

\vspace{{10mm}}

"""
    
    @staticmethod
    def get_document_footer() -> str:
        """Generate LaTeX document footer."""
        return r"""
\end{document}
"""


class AnkiConfig:
    """Anki export configuration."""
    
    # Anki LaTeX delimiters
    INLINE_MATH_START = "[$]"
    INLINE_MATH_END = "[/$]"
    DISPLAY_MATH_START = "[$$]"
    DISPLAY_MATH_END = "[/$$]"
    
    # Field separator
    FIELD_SEPARATOR = " | "
    
    # File header
    FILE_HEADER = """# Anki Import File - LaTeX Math Enabled
# Format: Question | Answer | Tags
"""
    
    @staticmethod
    def get_conversion_patterns() -> Dict[str, str]:
        """Get LaTeX to Anki conversion patterns."""
        return {
            'inline_start': AnkiConfig.INLINE_MATH_START,
            'inline_end': AnkiConfig.INLINE_MATH_END,
            'display_start': AnkiConfig.DISPLAY_MATH_START,
            'display_end': AnkiConfig.DISPLAY_MATH_END,
        }

