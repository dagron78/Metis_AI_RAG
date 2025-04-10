/**
 * Implementation of the HTML5 EventSource interface for server-sent events
 * This is a polyfill for fetch-based EventSource implementation
 */

function fetchEventSource(url, options = {}) {
  const { 
    method = 'GET',
    headers = {},
    body = null,
    signal = null,
    onopen = () => {},
    onmessage = () => {},
    onerror = () => {},
    onclose = () => {}
  } = options;

  const controller = new AbortController();
  const combinedSignal = signal 
    ? new AbortController().signal 
    : controller.signal;
  
  if (signal) {
    signal.addEventListener('abort', () => controller.abort());
  }

  (async function stream() {
    try {
      const response = await fetch(url, {
        method,
        headers,
        body,
        signal: combinedSignal,
        // Required for streaming responses
        cache: 'no-store',
        credentials: 'same-origin'
      });

      // Call onopen with the response
      onopen(response);
      
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status} ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log('Stream complete');
          break;
        }
        
        // Decode the chunk
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        
        // Process complete lines
        let newlineIndex;
        while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
          const line = buffer.substring(0, newlineIndex).trim();
          buffer = buffer.substring(newlineIndex + 1);
          
          if (line === '') continue; // Skip empty lines
          
          if (line.startsWith('data:')) {
            const eventData = line.substring(5).trim();
            // Process and dispatch event data
            onmessage({
              data: eventData
            });
          }
        }
      }
      
      // Stream closed normally
      onclose();
    } catch (err) {
      // Check if the error was due to abort
      if (err.name === 'AbortError') {
        console.log('Stream aborted by client');
      } else {
        console.error('Stream error:', err);
        onerror(err);
      }
    }
  })();
  
  // Return the controller to allow the caller to abort
  return {
    close: () => controller.abort()
  };
}

// Add to window for global access
window.fetchEventSource = fetchEventSource;