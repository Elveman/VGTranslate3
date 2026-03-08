// VGTranslate3 Web UI - Alpine.js component

function translationMonitor() {
    return {
        current: {
            original_image: '',
            bbox_image: '',
            result_image: '',
            blocks: [],
            metrics: {}
        },
        history: [],
        ws: null,
        ws_connected: false,

        init() {
            this.connectWebSocket();
        },

        connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const httpPort = parseInt(window.location.port) || 4405;
            const ws_port = httpPort + 1;
            const ws_url = `${protocol}//${window.location.hostname}:${ws_port}/`;
            
            console.log('Connecting to WebSocket:', ws_url);
            this.ws = new WebSocket(ws_url);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.ws_connected = true;
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'history') {
                        this.history = data.data || [];
                    } else {
                        this.current = data;
                        this.history.unshift(data);
                        if (this.history.length > 10) {
                            this.history.pop();
                        }
                    }
                } catch (e) {
                    console.error('Error parsing WebSocket message:', e);
                }
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.ws_connected = false;
                this.ws = null;
                setTimeout(() => this.connectWebSocket(), 3000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        },

        loadFromHistory(index) {
            if (index >= 0 && index < this.history.length) {
                this.current = this.history[index];
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        },

        getTranslation(block) {
            // Try to get translation in target language (default: English)
            const targetLang = 'en';
            if (block.translation) {
                if (typeof block.translation === 'string') {
                    return block.translation;
                }
                if (block.translation[targetLang]) {
                    return block.translation[targetLang];
                }
                // Try first available language
                const firstLang = Object.keys(block.translation)[0];
                if (firstLang) {
                    return block.translation[firstLang];
                }
            }
            return 'N/A';
        },

        async exportData() {
            try {
                const response = await fetch('/api/export', { method: 'POST' });
                if (!response.ok) {
                    throw new Error('Export failed');
                }
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `vgtranslate3_export_${new Date().toISOString().replace(/[:.]/g, '-')}.zip`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } catch (e) {
                console.error('Export error:', e);
                alert('Export failed: ' + e.message);
            }
        },

        clearHistory() {
            if (confirm('Clear translation history? This cannot be undone.')) {
                this.history = [];
                this.current = {};
            }
        }
    }
}
