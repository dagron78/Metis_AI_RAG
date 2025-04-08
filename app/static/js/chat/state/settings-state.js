/**
 * Settings State Management
 * Manages user settings for the chat interface
 */

/**
 * SettingsState class
 * Manages user settings for the chat interface
 */
class SettingsState {
  /**
   * Constructor
   * @param {Object} config - Configuration options
   */
  constructor(config = {}) {
    // Configuration with defaults
    this.config = {
      ...config
    };
    
    // Default settings
    this.defaults = {
      useRag: true,
      useStreaming: true,
      showRawOutput: false,
      showRawLlmOutput: false,
      showAdvanced: false,
      maxResults: 5,
      temperature: 0.7,
      model: 'llama3',
      showConversationSelector: true
    };
    
    // Initialize state
    this.state = { ...this.defaults };
    
    // Event listeners
    this.listeners = {
      stateChange: [],
      settingChanged: {}
    };
    
    // Load settings from localStorage
    this.loadFromLocalStorage();
  }
  
  /**
   * Load settings from localStorage
   */
  loadFromLocalStorage() {
    // Load each setting from localStorage
    this.state.useRag = localStorage.getItem('metis_use_rag') !== 'false';
    this.state.useStreaming = localStorage.getItem('metis_use_streaming') !== 'false';
    this.state.showRawOutput = localStorage.getItem('metis_show_raw_output') === 'true';
    this.state.showRawLlmOutput = localStorage.getItem('metis_show_raw_llm_output') === 'true';
    this.state.showAdvanced = localStorage.getItem('metis_show_advanced') === 'true';
    this.state.showConversationSelector = localStorage.getItem('show_conversation_selector') !== 'false';
    
    // Load numeric settings
    const maxResults = localStorage.getItem('metis_max_results');
    if (maxResults !== null) {
      this.state.maxResults = parseInt(maxResults, 10);
    }
    
    const temperature = localStorage.getItem('metis_temperature');
    if (temperature !== null) {
      this.state.temperature = parseFloat(temperature);
    }
    
    // Load model
    const model = localStorage.getItem('metis_model');
    if (model) {
      this.state.model = model;
    }
  }
  
  /**
   * Save settings to localStorage
   */
  saveToLocalStorage() {
    // Save each setting to localStorage
    localStorage.setItem('metis_use_rag', this.state.useRag);
    localStorage.setItem('metis_use_streaming', this.state.useStreaming);
    localStorage.setItem('metis_show_raw_output', this.state.showRawOutput);
    localStorage.setItem('metis_show_raw_llm_output', this.state.showRawLlmOutput);
    localStorage.setItem('metis_show_advanced', this.state.showAdvanced);
    localStorage.setItem('show_conversation_selector', this.state.showConversationSelector);
    
    // Save numeric settings
    localStorage.setItem('metis_max_results', this.state.maxResults);
    localStorage.setItem('metis_temperature', this.state.temperature);
    
    // Save model
    localStorage.setItem('metis_model', this.state.model);
  }
  
  /**
   * Get the current settings
   * @returns {Object} The current settings
   */
  getSettings() {
    return { ...this.state };
  }
  
  /**
   * Get a specific setting
   * @param {string} key - The setting key
   * @returns {*} The setting value
   */
  getSetting(key) {
    return this.state[key];
  }
  
  /**
   * Update settings
   * @param {Object} newSettings - The new settings to merge with the current settings
   */
  updateSettings(newSettings) {
    const oldState = { ...this.state };
    this.state = { ...this.state, ...newSettings };
    
    // Save to localStorage
    this.saveToLocalStorage();
    
    // Notify listeners
    this.notifyListeners('stateChange', this.state, oldState);
    
    // Notify specific setting listeners
    Object.keys(newSettings).forEach(key => {
      if (newSettings[key] !== oldState[key]) {
        this.notifySettingListeners(key, newSettings[key], oldState[key]);
      }
    });
  }
  
  /**
   * Update a single setting
   * @param {string} key - The setting key
   * @param {*} value - The new setting value
   */
  updateSetting(key, value) {
    this.updateSettings({ [key]: value });
  }
  
  /**
   * Reset settings to defaults
   */
  resetToDefaults() {
    this.updateSettings(this.defaults);
  }
  
  /**
   * Add an event listener for all settings changes
   * @param {Function} callback - The callback function
   * @returns {Function} A function to remove the listener
   */
  addChangeListener(callback) {
    if (!this.listeners.stateChange) {
      this.listeners.stateChange = [];
    }
    
    this.listeners.stateChange.push(callback);
    
    // Return a function to remove the listener
    return () => {
      this.removeChangeListener(callback);
    };
  }
  
  /**
   * Remove an event listener for all settings changes
   * @param {Function} callback - The callback function to remove
   */
  removeChangeListener(callback) {
    if (!this.listeners.stateChange) return;
    
    this.listeners.stateChange = this.listeners.stateChange.filter(cb => cb !== callback);
  }
  
  /**
   * Add an event listener for a specific setting change
   * @param {string} key - The setting key to listen for
   * @param {Function} callback - The callback function
   * @returns {Function} A function to remove the listener
   */
  addSettingListener(key, callback) {
    if (!this.listeners.settingChanged[key]) {
      this.listeners.settingChanged[key] = [];
    }
    
    this.listeners.settingChanged[key].push(callback);
    
    // Return a function to remove the listener
    return () => {
      this.removeSettingListener(key, callback);
    };
  }
  
  /**
   * Remove an event listener for a specific setting change
   * @param {string} key - The setting key to stop listening for
   * @param {Function} callback - The callback function to remove
   */
  removeSettingListener(key, callback) {
    if (!this.listeners.settingChanged[key]) return;
    
    this.listeners.settingChanged[key] = this.listeners.settingChanged[key].filter(cb => cb !== callback);
  }
  
  /**
   * Notify listeners of a state change
   * @param {string} event - The event that occurred
   * @param {Object} newState - The new state
   * @param {Object} oldState - The old state
   */
  notifyListeners(event, newState, oldState) {
    if (!this.listeners[event]) return;
    
    this.listeners[event].forEach(callback => {
      try {
        callback(newState, oldState);
      } catch (error) {
        console.error(`Error in ${event} listener:`, error);
      }
    });
  }
  
  /**
   * Notify listeners of a specific setting change
   * @param {string} key - The setting key that changed
   * @param {*} newValue - The new value
   * @param {*} oldValue - The old value
   */
  notifySettingListeners(key, newValue, oldValue) {
    if (!this.listeners.settingChanged[key]) return;
    
    this.listeners.settingChanged[key].forEach(callback => {
      try {
        callback(newValue, oldValue);
      } catch (error) {
        console.error(`Error in setting ${key} listener:`, error);
      }
    });
  }
}

// Create a singleton instance
const settingsState = new SettingsState();

// Export the singleton instance
export { settingsState };