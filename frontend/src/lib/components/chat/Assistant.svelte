<script lang="ts">
    import { onMount } from 'svelte';
    import { marked } from 'marked';
    import CustomTerms from './CustomTerms.svelte';

    const user_public_key = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApnhE8fu37rR2kHQM6k+S\n16qPjZNWnfYqETuG/j7DNlE74WPsp74awWNNg72byuK44TFVNCmqy6vz7b5i8VTe\nxrEvjM0y6ldBMou09ZQC3Z5kuWTJ1bDh07bH3Vj0FugJ3eulT+BXA2k1I+hwTfEa\nELkLjOb6Lt1a4gDs4OjFUAl4KyM/PRzR3uHR0+dilNuMJ/hrXMqFGaHOFqLNYjSD\n9omGjJVMShlO/xoZ07/CE1nKj/4fGFJFyxG7ZKLZoVsnE4NWEz35JwYmnbqJWGOZ\nBhWI1Zsw5cH8EWsJuG1f8KivgKahZS7IJe+rTm0BPHKSpPa3XY8P1DI1wyyKMhQ0\nNwIDAQAB\n-----END PUBLIC KEY-----"
    const user_private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCmeETx+7futHaQ\ndAzqT5LXqo+Nk1ad9ioRO4b+PsM2UTvhY+ynvhrBY02DvZvK4rjhMVU0KarLq/Pt\nvmLxVN7GsS+MzTLqV0Eyi7T1lALdnmS5ZMnVsOHTtsfdWPQW6And66VP4FcDaTUj\n6HBN8RoQuQuM5vou3VriAOzg6MVQCXgrIz89HNHe4dHT52KU24wn+GtcyoUZoc4W\nos1iNIP2iYaMlUxKGU7/GhnTv8ITWcqP/h8YUkXLEbtkotmhWycTg1YTPfknBiad\nuolYY5kGFYjVmzDlwfwRawm4bV/wqK+ApqFlLsgl76tObQE8cpKk9rddjw/UMjXD\nLIoyFDQ3AgMBAAECggEABdMNbn4FKHft8g3tacFQ/PS9wxFVpX84Z5PynDCr+dmL\nw84QOKpBG2UTEDnxGn8mQtLMDWAr1qZ0iWvw4Eq85KzMYhvH3UUiRdd3hGQiWYiy\nM35gRXbD3/l0Mr1rBOYnejlFdm79/GOQ9WmrjD6UT+N5kPt/42XhSSkJILFkPfGY\nXu82a9CqaCIhKfzrdL6vUeCz6rvXSZQ+Fsbusp/4WxLu9hsYCrQOsMRfkT8gYyDH\nsBoEPV0KjX8RHYtz5H4/vTCT/YM4thu9S8vtPXC+on45r9TvQzaXa/HrMeSLwXGP\nyvaechiZSzFrLP7HDQRyJZHMiS2OUgnbzGhXcIDwwQKBgQDhrhw1eD9xcogiI7wa\n1qkuCU75VLCZWkBTxpO6gEPZJlqkLy1EObkH7gc6tOaN+73kunfBUSLJyYPs6s+V\n6fl8hDi/ebRPz0FPC/HEeZovay6Xn7/nie+76MPs+GkHLx/X7Cc2MAvw9cWeKvDp\nzmPtlqtPQA+m9Q1fQ9L+2EyYoQKBgQC81bgtffYGdeRQqndCpQ+jnHt4keWrSDKD\nPfhbY5iVCaXIAzEWCshlydZvS6bkkrvZO0QC+A3jjUNiHN+4R2L65P+nq9LgAvsO\nU69r9eYYv4l52z5qgB821RrfJL+5jXkS6oeF7B2pU11BOu9qLl1V5f9A7kMQ8Pyq\nCIt3Yjjl1wKBgQCwRaNI7Fx5iyDjsY+6UtKf36tsugaaMVEvXlqDAK5+DSQdO7Aa\nqw9oLzY8V5IBcpEW98KUH4CRpjHCOoHbsX4qEMiWXkRFVjfHuyei8+xHf2tMCP4G\npsm2tw9Zp4m5j8hKiezyuUKKeh1Z9mZn6MpKiDXUV9Ah8yP3te03GtFxIQKBgQCv\n3yUwSXaQQdCpSHrWuUC9kwp0Gv4a7p0NGvRquXHsrRWYGVDoRJasJrXu5jjD/d2y\nzr3jPgBBhNnTUS0URnhrUEjDcwZt2JjWmR5yoIzzU8DIm2egbT+lJAlo9qMSQC8Z\nbRFXq7dccuYR0MAW1qPbUuDPKpmP98J64oZyZCq19QKBgF4NxofUMyVhYyrk9nIk\ncZzajUe4N6Pb8yaPZhILhu5ipb7/PG80zl9BKKqqv31lm589K+3xV+Ea28cWHVn0\nv+YqXd98DaGasbz3+bukmoR84j8FvFDggFVjtKmgSC/Cx3WWHHa0iXaOa+/rWtjU\nZVeh14z1EALyisAcMP+YdCmD\n-----END PRIVATE KEY-----"
    interface Message {
      role: 'user' | 'assistant';
      content: string;
    }
  
    let query = '';
    let mode = 'regex'; // Default mode
    let showDropdown = false;
    let messages: Message[] = [];
    let isLoading = false;
    let error: string | null = null;
    let thinkingInfo: {
      original: string;
      anonymized: string;
      report: string;
    } | null = null;
  
    // UI state
    let showCustomTerms = false;
  
    const API_URL = 'http://localhost:8000';
    const DEFAULT_PROVIDER = 'gemini';
    const DEFAULT_MODEL = 'gemini-2.0-flash';
    const DEFAULT_TEMPERATURE = 0.7;
    const DEFAULT_MAX_TOKENS = 1000;
  
    onMount(() => {
      messages = [
        {
          role: 'assistant',
          content:
            "Hello! I'm your secure AI assistant. Your queries will be anonymized before processing to protect sensitive information. How can I help you today?"
        }
      ];
    });
  
    function setMode(newMode: string) {
      mode = newMode;
    }

    function toggleDropdown() {
      showDropdown = !showDropdown;
    }

    function selectMode(newMode: string) {
      mode = newMode;
      showDropdown = false;
    }

    async function sendQuery() {
      if (!query.trim()) return;
  
      const userMessage = query;
      query = '';
  
      messages = [...messages, { role: 'user', content: userMessage }];
      isLoading = true;
      error = null;
      thinkingInfo = null;
  
      try {
        const url = `${API_URL}/process_secure_query`;
        const payload = {
        text: userMessage,
        mode: mode,
        public_key: user_public_key,
        private_key: user_private_key,
        provider: DEFAULT_PROVIDER,
        model: DEFAULT_MODEL,
        temperature: DEFAULT_TEMPERATURE,
        max_tokens: DEFAULT_MAX_TOKENS
        };
        
        const response = await fetch(url, {
        method: 'POST',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error(`API returned status ${response.status}`);
  
        const data = await response.json();
  
        // Temporary anonymization display
        thinkingInfo = {
          original: data.original_text,
          anonymized: data.anonymized_text,
          report: 'PII detection and anonymization complete.'
        };
  
        // Simulate brief "thinking" delay
        await new Promise((resolve) => setTimeout(resolve, 5000));
  
        // Final assistant response
        messages = [
          ...messages,
          {
            role: 'assistant',
            content: data.final_response
          }
        ];
      } catch (err: any) {
        console.error('Error calling API:', err);
        error = `Error: ${err.message}. Make sure the API server is running at ${API_URL}.`;
      } finally {
        isLoading = false;
        thinkingInfo = null;
      }
    }
  
    function handleKeydown(event: KeyboardEvent) {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendQuery();
      }
    }

    async function anonymizeImage() {
      try {
        const formData = new FormData();
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.onchange = async () => {
          const file = fileInput.files[0];
          if (file) {
            formData.append('file', file);
            const response = await fetch(`${API_URL}/anonymize_image`, {
              method: 'POST',
              body: formData
            });
            if (!response.ok) throw new Error(`API returned status ${response.status}`);
            const imageBlob = await response.blob();
            const imageUrl = URL.createObjectURL(imageBlob);
            window.open(imageUrl, '_blank');
          }
        };
        fileInput.click();
      } catch (err) {
        console.error('Error calling anonymize_image API:', err);
        error = `Error: ${err.message}. Make sure the API server is running at ${API_URL}.`;
      }
    }

    function toggleCustomTerms() {
      showCustomTerms = !showCustomTerms;
    }
  </script>
  
  

    <!-- Main container with improved layout -->
    <div class="w-full flex flex-col lg:flex-row lg:space-x-8">
  <!-- Chat container -->
    <div class="flex-grow max-w-4xl mx-auto w-full">
      <div class="card-blur shadow-2xl overflow-hidden ">
        <div class="absolute top-4 right-4 z-10">
          <!-- Mode Selection Dropdown -->
          <div class="relative">
            <button on:click={toggleDropdown} class="px-4 py-2 bg-black bg-opacity-50 text-white rounded-lg shadow-md">
              {#if mode === 'regex'}
                Ninja Mode
              {:else if mode === 'ner'}
                Spyglass Mode
              {:else if mode === 'llm'}
                Blacksite Mode
              {/if}
            </button>
            {#if showDropdown}
              <div class="absolute right-0 mt-2 w-48 bg-black bg-opacity-70 text-white rounded-lg shadow-lg">
                <div on:click={() => selectMode('regex')} class="px-4 py-2 hover:bg-gray-700 cursor-pointer">
                  <strong>Ninja Mode</strong><br><span class="text-xs">Fast but shallow cuts</span>
                </div>
                <div on:click={() => selectMode('ner')} class="px-4 py-2 hover:bg-gray-700 cursor-pointer">
                  <strong>Spyglass Mode</strong><br><span class="text-xs">Peering into context</span>
                </div>
                <div on:click={() => selectMode('llm')} class="px-4 py-2 hover:bg-gray-700 cursor-pointer">
                  <strong>Blacksite Mode</strong><br><span class="text-xs">Deep ops, nothing leaks out</span>
                </div>
              </div>
            {/if}
          </div>
        </div>
      <div class="card-blur shadow-2xl  overflow-hidden">
      
        <!-- Chat Messages Container with Blurry Effect -->
        <div class="h-[500px] overflow-y-auto p-6 space-y-4 backdrop-blur-xl bg-opacity-20 bg-purple-950">
          {#each messages as message}
            <div class="chat-message {message.role === 'user' ? 'flex justify-end' : ''}">
              <div class="{message.role === 'user' 
                ? 'bg-purple-800 bg-opacity-60 backdrop-blur-xs ml-12 rounded-lg p-4 max-w-[80%] shadow-lg' 
                : 'bg-purple-900 bg-opacity-50 backdrop-blur-xs mr-12 border-l-4 border-neon-purple rounded-lg p-4 max-w-[80%] shadow-lg'}">
                <p class="text-slate-100">{@html marked(message.content)}</p>
              </div>
            </div>
          {/each}
      
          <!-- Thinking & Loading States -->
          {#if thinkingInfo}
            <div class="bg-purple-800 bg-opacity-40 backdrop-blur-xs border-l-4 border-neon-pink text-slate-200 p-4 rounded-md space-y-2 text-sm mr-12 shadow-lg">
              <p class="font-bold flex items-center"><span class="text-neon-pink mr-2">🔒</span> Anonymizing your message securely...</p>
              <div class="space-y-1 bg-purple-900 bg-opacity-60 p-3 rounded-md">
                <p><span class="font-semibold text-neon-blue">Original:</span> {thinkingInfo.original}</p>
                <p><span class="font-semibold text-neon-blue">Anonymized:</span> {thinkingInfo.anonymized}</p>
                <p><span class="font-semibold text-neon-blue">Report:</span> {thinkingInfo.report}</p>
              </div>
            </div>
          {:else if isLoading}
            <div class="flex items-center space-x-2 mr-12 bg-purple-800 bg-opacity-40 backdrop-blur-xs border-l-4 border-neon-blue rounded-lg p-4 shadow-lg">
              <div class="animate-pulse flex space-x-1">
                <div class="h-2 w-2 bg-neon-blue rounded-full"></div>
                <div class="h-2 w-2 bg-neon-blue rounded-full animation-delay-200"></div>
                <div class="h-2 w-2 bg-neon-blue rounded-full animation-delay-400"></div>
              </div>
              <span class="text-purple-200">Thinking...</span>
            </div>
          {/if}
      
          {#if error}
            <div class="bg-red-900 bg-opacity-40 backdrop-blur-xs border-l-4 border-red-500 text-white p-4 rounded-lg mr-12 shadow-lg">
              <p class="font-medium">{error}</p>
            </div>
          {/if}
        </div>
      
        <!-- Input Area with enhanced blur -->
        <div class="p-4 backdrop-blur-xl bg-purple-950 bg-opacity-30 border-t border-purple-700 border-opacity-40">
          <div class="flex space-x-2">
            <textarea
              bind:value={query}
              on:keydown={handleKeydown}
              placeholder="Type your message here... (Press Enter to send)"
              rows="2"
              class="flex-1 px-4 py-3 bg-dark bg-opacity-80 text-purple-100 rounded-lg border border-purple-700 focus:ring-2 focus:ring-neon-purple focus:outline-none resize-none"
            ></textarea>
            <button
              on:click={sendQuery}
              class="px-6 py-2 bg-gradient-to-r from-neon-purple to-neon-blue hover:opacity-90 text-white font-medium rounded-lg shadow transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-w-[80px]"
              disabled={isLoading || !query.trim()}
            >
              {#if isLoading}
                <div class="h-5 w-5 border-t-2 border-b-2 border-white rounded-full animate-spin"></div>
              {:else}
                Send
              {/if}
            </button>
          <button
              on:click={anonymizeImage}
              class="px-6 py-2 bg-gradient-to-r from-neon-purple to-neon-blue hover:opacity-90 text-white font-medium rounded-lg shadow transition-all flex items-center justify-center min-w-[80px]"
            >
              Anonymize Image
            </button>
          </div>
      
          <!-- Footer with toggle for custom terms -->
          <footer class="mt-4 flex justify-between items-center text-xs text-purple-400">
            <div>
              Using {DEFAULT_PROVIDER} • Model: {DEFAULT_MODEL} •
              <a
                href="http://localhost:8000/docs"
                class="text-neon-blue hover:text-neon-purple transition-colors"
                target="_blank"
                rel="noopener noreferrer"
              >API Docs</a>
            </div>
            <button 
              on:click={toggleCustomTerms}
              class="text-neon-blue hover:text-neon-purple transition-colors flex items-center"
            >
              <span class="mr-1">{showCustomTerms ? 'Hide' : 'Show'} Custom Terms</span>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </footer>
        </div>
      </div>
    </div>
    </div>
  
    
    <!-- Custom Terms Panel (conditionally shown) -->
    {#if showCustomTerms}
      <div class="mt-6 lg:mt-0 w-full lg:w-80 hidden lg:block">
    <div class="card-blur p-4">
      <CustomTerms />
    </div>
  </div>
    {/if}
  </div>
  
  
  <!-- Mobile version of custom terms (shown as modal) -->
  {#if showCustomTerms}
    <div class="lg:hidden fixed inset-0 bg-black bg-opacity-70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="w-full max-w-md">
        <div class="relative">
          <button 
            on:click={toggleCustomTerms} 
            class="absolute top-2 right-2 text-purple-200 hover:text-white"
            aria-label="Close custom terms panel"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <CustomTerms />
        </div>
      </div>
    </div>
  {/if}
  
  <style>
    .animation-delay-200 {
      animation-delay: 0.2s;
    }
    .animation-delay-400 {
      animation-delay: 0.4s;
    }
  </style>
  