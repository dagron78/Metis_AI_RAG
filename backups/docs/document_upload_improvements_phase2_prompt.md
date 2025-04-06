# Metis RAG Document Upload Improvements - Phase 2 Prompt

## Overview

Now that we've completed Phase 1 of the document upload improvements, which fixed the multiple file selection issue and enhanced file validation, we're ready to move on to Phase 2. This phase will focus on improving the user experience (UX) of the document upload process.

## Phase 2 Goals

1. **Redesign the File Selection Interface**
   - Create a more intuitive and visually appealing file selection area
   - Implement drag-and-drop functionality across the entire upload area
   - Add file preview capabilities for selected documents
   - Improve visual feedback during the selection process

2. **Implement Batch Actions**
   - Add ability to apply tags to multiple selected files at once
   - Enable folder assignment for multiple files simultaneously
   - Implement batch deletion with confirmation
   - Add batch processing options with configurable parameters

3. **Improve Progress Indicators**
   - Redesign progress bars with more detailed information
   - Add individual file progress tracking with status indicators
   - Implement overall batch progress visualization
   - Add estimated time remaining for uploads

## Implementation Approach

### 1. File Selection Interface Redesign

The current file selection interface is functional but could be more intuitive. We should:

- Create a modern drag-and-drop zone that highlights when files are dragged over it
- Add file preview thumbnails for common file types (PDF, DOCX, etc.)
- Display file metadata (size, type, last modified) in the selection list
- Implement a grid/list view toggle for selected files
- Add the ability to reorder files before upload

### 2. Batch Actions Implementation

Currently, users need to perform actions on files individually. We should:

- Add a multi-select mechanism with checkboxes for files
- Create a batch actions toolbar that appears when multiple files are selected
- Implement batch tagging with tag suggestions based on file content
- Add batch folder assignment with folder browser/creation
- Create confirmation dialogs for destructive batch actions

### 3. Progress Indicators Enhancement

The current progress indicators are basic. We should:

- Redesign progress bars with animated fills and percentage displays
- Add status icons for different stages (queued, uploading, processing, complete, error)
- Implement a detailed progress panel that can be expanded/collapsed
- Add upload speed and time remaining estimates
- Create a summary view for completed uploads with success/failure counts

## Technical Considerations

- Use modern CSS features (Grid, Flexbox, CSS Variables) for responsive layouts
- Implement client-side file handling with the File API
- Use requestAnimationFrame for smooth progress animations
- Consider using Web Workers for background processing of large files
- Implement proper error handling and recovery mechanisms

## Success Criteria

- Users can easily select and upload multiple files with clear visual feedback
- Batch operations work correctly and save time compared to individual operations
- Progress indicators provide accurate and helpful information during uploads
- The interface is responsive and works well on different screen sizes
- Error states are clearly communicated with actionable recovery options

## Getting Started

To begin Phase 2, we should:

1. Create wireframes or mockups of the new interface
2. Identify the key components that need to be built or modified
3. Develop a prototype of the new file selection interface
4. Implement the batch actions functionality
5. Enhance the progress indicators
6. Test the new features with real users
7. Refine based on feedback

Let's start by exploring modern file upload interfaces for inspiration and then create a design prototype for our improved document upload experience.