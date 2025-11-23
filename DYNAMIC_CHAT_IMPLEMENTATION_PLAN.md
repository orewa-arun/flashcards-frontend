# Dynamic Chat Implementation Plan: LaTeX and Matplotlib Diagrams

This document outlines the complete plan for enhancing the AI Tutor's chat functionality to support rich content, including mathematical formulas (via LaTeX) and dynamically generated diagrams (via Matplotlib and Cloudflare R2).

## High-Level Goal

To create a context-aware, dynamic chat experience where the AI can intuitively decide to render mathematical formulas, diagrams, and other rich media to best explain concepts. The user should see a seamless blend of text, formulas, and images without being exposed to the underlying code or complexity.

---

## Phase 1: LaTeX Integration (Quick Win)

This phase focuses on enabling the rendering of mathematical notation directly in the React frontend.

### Backend Responsibilities

1.  **Prompt Engineering**:
    *   Update the core AI Tutor system prompt to instruct the Large Language Model (LLM) to use standard LaTeX delimiters for mathematical notation.
    *   **Inline Formulas**: Use `\( ... \)` (e.g., `The formula is \(E = mc^2\).`).
    *   **Block Formulas**: Use `$$ ... $$` for standalone equations.
2.  **API Response**:
    *   The backend chat API will return messages as plain text strings. No special backend processing is required for LaTeX content itself; it will be passed directly to the frontend.

### Frontend (React) Responsibilities

1.  **Install Dependencies**:
    *   Add `react-katex` and `katex` to `frontend/package.json`.
    *   Command: `npm install react-katex katex`

2.  **Import KaTeX CSS**:
    *   In the main application entry point (e.g., `frontend/src/main.jsx` or `frontend/src/index.jsx`), import the KaTeX stylesheet to ensure formulas are rendered correctly:
        ```javascript
        import 'katex/dist/katex.min.css';
        ```

3.  **Create a `ContentRenderer` Component**:
    *   Create a new component (`frontend/src/components/ContentRenderer.jsx`) responsible for parsing and rendering message content.
    *   This component will accept a string as a prop.
    *   It will parse the string for LaTeX delimiters (`\(...\)` and `$$...$$`).
    *   It will map over the parsed segments and render them accordingly:
        *   Plain text segments are rendered as-is.
        *   Inline math segments are rendered using the `<InlineMath>` component from `react-katex`.
        *   Block math segments are rendered using the `<BlockMath>` component from `react-katex`.

4.  **Update the Chat Message Component**:
    *   Identify the existing component responsible for displaying a single chat message.
    *   Instead of rendering the message text directly, it will now pass the text to the new `ContentRenderer` component.

---

## Phase 2: Dynamic Diagram Generation (Visual Leap)

This phase introduces the capability for the AI to generate and display Python-based `matplotlib` diagrams.

### Backend Responsibilities

1.  **Add Dependencies**:
    *   Add `boto3` to `backend/requirements.txt` to enable interaction with Cloudflare R2's S3-compatible API.

2.  **Cloudflare R2 Setup**:
    *   Configure the backend environment (e.g., in Railway and a local `.env` file) with the following credentials for the R2 bucket:
        *   `CLOUDFLARE_R2_ACCESS_KEY_ID`
        *   `CLOUDFLARE_R2_SECRET_ACCESS_KEY`
        *   `CLOUDFLARE_R2_ENDPOINT_URL`
        *   `CLOUDFLARE_R2_BUCKET_NAME`

3.  **Enhanced AI Logic & Prompting**:
    *   The LLM's prompt will be engineered to follow a "thought process":
        1.  **Decide**: "Is a visual diagram necessary to explain this concept effectively?"
        2.  **Act**: If yes, generate a self-contained, executable Python script using `matplotlib` that saves a plot to a file (e.g., `output.png`).
        3.  **Explain**: Generate a textual explanation that accompanies the diagram.

4.  **Structured API Response**:
    *   The backend will no longer send plain text for all messages. It will use a structured JSON format to differentiate content types.

    *   **Text/Math Message:**
        ```json
        {
          "type": "text",
          "content": "The formula for gravitational force is $$ F = G \\frac{m_1 m_2}{r^2} $$"
        }
        ```
    *   **Diagram Message:**
        ```json
        {
          "type": "diagram",
          "imageUrl": "https://<your-r2-url>/diagrams/unique_id.png",
          "explanation": "This diagram shows the relationship between..."
        }
        ```

5.  **Secure Code Execution Sandbox**:
    *   Set up an isolated, secure environment (e.g., using Docker) to execute the LLM-generated Python code.
    *   This sandbox will have Python, `matplotlib`, `numpy`, etc., pre-installed.
    *   It will execute the script, capture the output image, and then be terminated.

6.  **Image Upload to R2**:
    *   After the image is generated in the sandbox, the backend will use `boto3` to upload the image file to the configured Cloudflare R2 bucket.
    *   The image will be given a unique name (e.g., using a UUID) and made publicly readable.
    *   The public URL of the uploaded image will be used in the `imageUrl` field of the API response.

### Frontend (React) Responsibilities

1.  **Update Chat Component Logic**:
    *   The main chat message component will be updated to handle the new structured JSON response.
    *   It will use conditional logic based on the `type` field:
        *   If `type === 'text'`, it will render the `content` using the `ContentRenderer` component from Phase 1.
        *   If `type === 'diagram'`, it will:
            *   Render an `<img>` tag with its `src` set to the `imageUrl`.
            *   Display a loading indicator while the image is being fetched.
            *   Render the `explanation` text below the image, passing it through the `ContentRenderer` (as explanations may also contain LaTeX).

This comprehensive plan ensures a phased, manageable approach to building a highly dynamic and effective AI-powered chat interface.

