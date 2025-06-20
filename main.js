// JavaScript for Automated Video Generator
// Handles user interface interactions and API communication

class VideoGenerator {
    constructor() {
        this.currentJob = null;
        this.voiceSamplePath = null;
        this.progressInterval = null;
        
        this.initializeEventListeners();
        this.initializeTabs();
    }

    initializeEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Article preview
        document.getElementById('preview-btn').addEventListener('click', () => {
            this.previewArticle();
        });

        // Voice upload and testing
        document.getElementById('voice-upload').addEventListener('change', (e) => {
            this.handleVoiceUpload(e.target.files[0]);
        });

        document.getElementById('test-voice-btn').addEventListener('click', () => {
            this.testVoiceClone();
        });

        // Main generation button
        document.getElementById('generate-btn').addEventListener('click', () => {
            this.generateVideo();
        });

        // Action buttons
        document.getElementById('download-btn').addEventListener('click', () => {
            this.downloadVideo();
        });

        document.getElementById('new-video-btn').addEventListener('click', () => {
            this.resetInterface();
        });

        document.getElementById('retry-btn').addEventListener('click', () => {
            this.resetInterface();
        });
    }

    initializeTabs() {
        // Set initial tab state
        this.switchTab('text');
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    async previewArticle() {
        const url = document.getElementById('url-input').value.trim();
        
        if (!url) {
            this.showError('Please enter a valid URL');
            return;
        }

        if (!this.isValidUrl(url)) {
            this.showError('Please enter a valid URL');
            return;
        }

        this.showLoading('Extracting article...');

        try {
            const response = await fetch('/api/scrape_article', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();
            this.hideLoading();

            if (response.ok) {
                this.displayArticlePreview(data);
            } else {
                this.showError(data.error || 'Failed to extract article');
            }

        } catch (error) {
            this.hideLoading();
            this.showError('Failed to extract article: ' + error.message);
        }
    }

    displayArticlePreview(data) {
        document.getElementById('preview-title').textContent = data.title || 'No title';
        document.getElementById('preview-author').textContent = data.author || 'Unknown author';
        document.getElementById('preview-text').textContent = data.text || 'No content extracted';
        
        const imageElement = document.getElementById('preview-image');
        if (data.top_image) {
            imageElement.src = data.top_image;
            imageElement.style.display = 'block';
        } else {
            imageElement.style.display = 'none';
        }

        document.getElementById('article-preview').style.display = 'block';
    }

    async handleVoiceUpload(file) {
        if (!file) return;

        if (!file.type.startsWith('audio/')) {
            this.showError('Please upload an audio file');
            return;
        }

        if (file.size > 10 * 1024 * 1024) { // 10MB limit
            this.showError('Audio file too large. Please use a file under 10MB');
            return;
        }

        this.showLoading('Processing voice sample...');

        const formData = new FormData();
        formData.append('audio', file);

        try {
            const response = await fetch('/api/voice_clone', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            this.hideLoading();

            if (response.ok) {
                this.voiceSamplePath = data.voice_sample_path;
                document.getElementById('test-voice-btn').style.display = 'inline-block';
                
                // Play test audio if available
                if (data.test_audio_url) {
                    const audioPlayer = document.getElementById('voice-test-player');
                    audioPlayer.src = data.test_audio_url;
                    audioPlayer.style.display = 'block';
                }

                this.showSuccess('Voice sample uploaded successfully!');
            } else {
                this.showError(data.error || 'Failed to process voice sample');
            }

        } catch (error) {
            this.hideLoading();
            this.showError('Failed to upload voice sample: ' + error.message);
        }
    }

    async testVoiceClone() {
        if (!this.voiceSamplePath) {
            this.showError('Please upload a voice sample first');
            return;
        }

        const audioPlayer = document.getElementById('voice-test-player');
        if (audioPlayer.src) {
            audioPlayer.play();
        }
    }

    async generateVideo() {
        const data = this.collectFormData();
        
        if (!this.validateFormData(data)) {
            return;
        }

        this.showProgressSection();
        this.updateProgress(0, 'Starting video generation...');

        try {
            const response = await fetch('/api/generate_video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                this.currentJob = result.job_id;
                this.startProgressPolling();
            } else {
                this.showErrorSection(result.error || 'Failed to start video generation');
            }

        } catch (error) {
            this.showErrorSection('Failed to generate video: ' + error.message);
        }
    }

    collectFormData() {
        const activeTab = document.querySelector('.tab-button.active').dataset.tab;
        const data = {
            voice_sample: this.voiceSamplePath,
            language: document.getElementById('language-select').value,
            max_slides: parseInt(document.getElementById('max-slides').value),
            words_per_slide: parseInt(document.getElementById('words-per-slide').value)
        };

        if (activeTab === 'text') {
            data.text = document.getElementById('text-input').value.trim();
            data.title = document.getElementById('text-title').value.trim();
            data.author = document.getElementById('text-author').value.trim();
        } else if (activeTab === 'url') {
            data.url = document.getElementById('url-input').value.trim();
        }

        return data;
    }

    validateFormData(data) {
        if (!data.text && !data.url) {
            this.showError('Please provide either text content or a URL');
            return false;
        }

        if (data.text && data.text.length < 50) {
            this.showError('Text content must be at least 50 characters long');
            return false;
        }

        if (data.url && !this.isValidUrl(data.url)) {
            this.showError('Please provide a valid URL');
            return false;
        }

        return true;
    }

    startProgressPolling() {
        this.progressInterval = setInterval(() => {
            this.checkJobStatus();
        }, 2000); // Check every 2 seconds
    }

    async checkJobStatus() {
        if (!this.currentJob) return;

        try {
            const response = await fetch(`/api/job_status/${this.currentJob}`);
            const data = await response.json();

            if (response.ok) {
                this.updateProgress(data.progress, data.message);
                this.updateProgressSteps(data.progress);

                if (data.status === 'completed') {
                    clearInterval(this.progressInterval);
                    this.showResultsSection(data);
                } else if (data.status === 'error') {
                    clearInterval(this.progressInterval);
                    this.showErrorSection(data.message);
                }
            }

        } catch (error) {
            console.error('Error checking job status:', error);
        }
    }

    updateProgress(percentage, message) {
        document.getElementById('progress-fill').style.width = percentage + '%';
        document.getElementById('progress-text').textContent = message;
    }

    updateProgressSteps(percentage) {
        const steps = ['step-content', 'step-audio', 'step-images', 'step-video'];
        const stepPercentages = [25, 50, 75, 100];

        steps.forEach((stepId, index) => {
            const step = document.getElementById(stepId);
            if (percentage >= stepPercentages[index]) {
                step.classList.add('completed');
                step.classList.remove('active');
            } else if (percentage >= (stepPercentages[index] - 25)) {
                step.classList.add('active');
                step.classList.remove('completed');
            } else {
                step.classList.remove('active', 'completed');
            }
        });
    }

    showProgressSection() {
        document.getElementById('progress-section').style.display = 'block';
        document.getElementById('results-section').style.display = 'none';
        document.getElementById('error-section').style.display = 'none';
        
        // Scroll to progress section
        document.getElementById('progress-section').scrollIntoView({ 
            behavior: 'smooth' 
        });
    }

    showResultsSection(data) {
        document.getElementById('progress-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'block';
        document.getElementById('error-section').style.display = 'none';

        // Set up video player
        const video = document.getElementById('generated-video');
        video.src = data.download_url;

        // Update download button
        document.getElementById('download-btn').onclick = () => {
            window.open(data.download_url, '_blank');
        };

        // Scroll to results
        document.getElementById('results-section').scrollIntoView({ 
            behavior: 'smooth' 
        });
    }

    showErrorSection(message) {
        document.getElementById('progress-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'none';
        document.getElementById('error-section').style.display = 'block';
        
        document.getElementById('error-message').textContent = message;
        
        document.getElementById('error-section').scrollIntoView({ 
            behavior: 'smooth' 
        });
    }

    downloadVideo() {
        if (this.currentJob) {
            window.open(`/api/download/${this.currentJob}`, '_blank');
        }
    }

    resetInterface() {
        // Clear form data
        document.getElementById('text-input').value = '';
        document.getElementById('text-title').value = '';
        document.getElementById('text-author').value = '';
        document.getElementById('url-input').value = '';
        
        // Reset voice upload
        document.getElementById('voice-upload').value = '';
        document.getElementById('test-voice-btn').style.display = 'none';
        document.getElementById('voice-test-player').style.display = 'none';
        this.voiceSamplePath = null;
        
        // Hide sections
        document.getElementById('progress-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'none';
        document.getElementById('error-section').style.display = 'none';
        document.getElementById('article-preview').style.display = 'none';
        
        // Clear job
        this.currentJob = null;
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        
        // Reset to first tab
        this.switchTab('text');
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        overlay.querySelector('p').textContent = message;
        overlay.style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading-overlay').style.display = 'none';
    }

    showError(message) {
        alert('Error: ' + message);
    }

    showSuccess(message) {
        // You could implement a toast notification here
        console.log('Success: ' + message);
    }

    isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }
}

// Utility functions
function showAbout() {
    document.getElementById('about-modal').style.display = 'flex';
}

function hideAbout() {
    document.getElementById('about-modal').style.display = 'none';
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new VideoGenerator();
});

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('about-modal');
    if (e.target === modal) {
        hideAbout();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Escape key closes modal
    if (e.key === 'Escape') {
        hideAbout();
    }
    
    // Ctrl/Cmd + Enter to generate video
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        document.getElementById('generate-btn').click();
    }
});