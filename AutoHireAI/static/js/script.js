// Global state for the app
const appState = {
    jobDescription: null,
    candidates: [],
    shortlistedCandidates: [],
    currentStep: 1
};

// DOM elements
const stepIndicators = [
    document.getElementById('step1-indicator'),
    document.getElementById('step2-indicator'),
    document.getElementById('step3-indicator'),
    document.getElementById('step4-indicator')
];

const stepContents = [
    document.getElementById('step1-content'),
    document.getElementById('step2-content'),
    document.getElementById('step3-content'),
    document.getElementById('step4-content')
];

// Set min date to today for interview scheduling
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('interview-date')) {
        document.getElementById('interview-date').min = new Date().toISOString().split('T')[0];
    }

    initializeEventListeners();
});

// Initialize all event listeners
function initializeEventListeners() {
    // Job Description Upload functionality
    const jdUploadArea = document.getElementById('jd-upload-area');
    const jdUploadInput = document.getElementById('jd-upload');
    
    if (jdUploadArea && jdUploadInput) {
        jdUploadArea.addEventListener('click', () => {
            jdUploadInput.click();
        });
        
        jdUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            jdUploadArea.classList.add('dragover');
        });
        
        jdUploadArea.addEventListener('dragleave', () => {
            jdUploadArea.classList.remove('dragover');
        });
        
        jdUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            jdUploadArea.classList.remove('dragover');
            handleJDUpload(e.dataTransfer.files[0]);
        });

        jdUploadInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleJDUpload(e.target.files[0]);
            }
        });
    }

    // Button to proceed from Step 1 to Step 2
    const nextStep1Button = document.getElementById('next-step1');
    if (nextStep1Button) {
        nextStep1Button.addEventListener('click', () => {
            navigateToStep(2);
        });
    }

    // CV Upload functionality
    const cvUploadArea = document.getElementById('cv-upload-area');
    const cvUploadInput = document.getElementById('cv-upload');
    
    if (cvUploadArea && cvUploadInput) {
        cvUploadArea.addEventListener('click', () => {
            cvUploadInput.click();
        });
        
        cvUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            cvUploadArea.classList.add('dragover');
        });
        
        cvUploadArea.addEventListener('dragleave', () => {
            cvUploadArea.classList.remove('dragover');
        });
        
        cvUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            cvUploadArea.classList.remove('dragover');
            handleCVFiles(e.dataTransfer.files);
        });

        cvUploadInput.addEventListener('change', (e) => {
            handleCVFiles(e.target.files);
        });
    }

    // Button to process CVs and proceed to Step 3
    const processCVsButton = document.getElementById('process-cvs');
    if (processCVsButton) {
        processCVsButton.addEventListener('click', () => {
            processCVs();
        });
    }

    // Button to proceed from Step 3 to Step 4
    const nextStep3Button = document.getElementById('next-step3');
    if (nextStep3Button) {
        nextStep3Button.addEventListener('click', () => {
            navigateToStep(4);
            displayShortlistedCandidates();
        });
    }

    // Button to generate interview slots
    const generateSlotsButton = document.getElementById('generate-slots');
    if (generateSlotsButton) {
        generateSlotsButton.addEventListener('click', () => {
            generateInterviewSlots();
        });
    }

    // Button to send interview invites
    const sendInvitesButton = document.getElementById('send-invites');
    if (sendInvitesButton) {
        sendInvitesButton.addEventListener('click', () => {
            sendInterviewInvites();
        });
    }

    // Button to restart the process
    const restartProcessButton = document.getElementById('restart-process');
    if (restartProcessButton) {
        restartProcessButton.addEventListener('click', () => {
            resetProcess();
        });
    }
}

// Handle Job Description File Upload
async function handleJDUpload(file) {
    if (!file) return;
    
    document.getElementById('jd-filename').textContent = file.name;
    
    try {
        // Show loading animation
        document.getElementById('jd-loading').classList.remove('hidden');
        document.getElementById('jd-preview').classList.add('hidden');
        document.getElementById('jd-upload-area').style.opacity = '0.5';
        document.getElementById('jd-upload-area').style.pointerEvents = 'none';
        
        // Create FormData and append the file
        const formData = new FormData();
        formData.append('file', file);
        
        // Send to backend for processing
        const response = await fetch('/api/process-job-description', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to process job description');
        }
        
        const data = await response.json();
        appState.jobDescription = data;
        
        // Update JD summary UI
        updateJobDescriptionSummary(data);
        document.getElementById('jd-preview').classList.remove('hidden');
        
        showNotification('Success', 'Job description processed successfully!', 'success');
    } catch (error) {
        console.error('Error processing job description:', error);
        showNotification('Error', error.message, 'error');
    } finally {
        // Hide loading animation and reset UI
        document.getElementById('jd-loading').classList.add('hidden');
        document.getElementById('jd-upload-area').style.opacity = '1';
        document.getElementById('jd-upload-area').style.pointerEvents = 'auto';
    }
}

// Update the job description summary in the UI
function updateJobDescriptionSummary(jdData) {
    const summaryElement = document.querySelector('.jd-summary');
    if (!summaryElement) return;
    
    // Update position
    document.getElementById('jd-position').textContent = jdData.position || 'Not specified';
    
    // Update requirements list
    const requirementsElement = document.getElementById('jd-requirements');
    requirementsElement.innerHTML = '';
    
    if (jdData.requirements && jdData.requirements.length > 0) {
        jdData.requirements.forEach(req => {
            const li = document.createElement('li');
            li.textContent = req;
            requirementsElement.appendChild(li);
        });
    } else {
        const li = document.createElement('li');
        li.textContent = 'No specific requirements found';
        requirementsElement.appendChild(li);
    }
}

// Handle multiple CV file uploads
function handleCVFiles(files) {
    if (!files || files.length === 0) return;
    
    const cvFileList = document.getElementById('cv-file-list');
    const cvPreview = document.getElementById('cv-preview');
    
    // Get existing file names
    const existingFiles = new Set(
        Array.from(cvFileList.querySelectorAll('.file-item'))
            .map(item => item.querySelector('.file-name').textContent)
    );
    
    // Update file count header or create if doesn't exist
    let countHeader = cvFileList.querySelector('.file-count');
    if (!countHeader) {
        countHeader = document.createElement('div');
        countHeader.className = 'file-count';
        countHeader.style.marginBottom = '10px';
        countHeader.style.fontWeight = '500';
        cvFileList.insertBefore(countHeader, cvFileList.firstChild);
    }
    
    // Handle multiple files, skip duplicates
    Array.from(files).forEach(file => {
        if (!existingFiles.has(file.name)) {
            existingFiles.add(file.name);
            // Store the file for later processing
            appState.candidates.push({
                file: file,
                filename: file.name,
                fileSize: formatFileSize(file.size)
            });
            
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <div class="file-icon">
                    <i class="fas fa-file-pdf"></i>
                </div>
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            `;
            cvFileList.appendChild(fileItem);
        }
    });
    
    // Update the count after adding new files
    const totalFiles = cvFileList.querySelectorAll('.file-item').length;
    countHeader.textContent = `Selected CVs: ${totalFiles}`;
    
    cvPreview.classList.remove('hidden');
}

// Process uploaded CVs
async function processCVs() {
    if (appState.candidates.length === 0) {
        showNotification('Error', 'Please upload at least one CV first', 'error');
        return;
    }
    
    if (!appState.jobDescription) {
        showNotification('Error', 'Job description data is missing. Please upload a job description first.', 'error');
        return;
    }
    
    try {
        navigateToStep(3);
        document.getElementById('matching-loading').style.display = 'block';
        document.getElementById('progress-container').classList.add('hidden');
        document.getElementById('results-container').classList.add('hidden');
        
        // Process each candidate one by one
        const totalCandidates = appState.candidates.length;
        
        for (let i = 0; i < totalCandidates; i++) {
            const candidate = appState.candidates[i];
            if (!candidate.processed) {
                await processSingleCV(candidate, i, totalCandidates);
                updateProgressUI(i + 1, totalCandidates);
            }
        }
        
        // Sort candidates by score (descending)
        appState.candidates.sort((a, b) => b.score - a.score);
        
        // Identify shortlisted candidates (score >= 80)
        appState.shortlistedCandidates = appState.candidates.filter(c => c.score >= 80);
        
        // Display results
        displayResults();
    } catch (error) {
        console.error('Error processing CVs:', error);
        showNotification('Error', error.message, 'error');
        // Reset to step 2 on error
        navigateToStep(2);
    }
}

// Process a single CV
async function processSingleCV(candidate, index, total) {
    // Show progress for this candidate
    document.getElementById('matching-loading').style.display = 'none';
    document.getElementById('progress-container').classList.remove('hidden');
    updateProgressUI(index, total);
    
    try {
        // Create FormData and append the file
        const formData = new FormData();
        formData.append('file', candidate.file);
        formData.append('job_description', JSON.stringify(appState.jobDescription));
        
        // Send to backend for processing
        const response = await fetch('/api/process-cv', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to process CV');
        }
        
        const data = await response.json();
        
        // Update candidate with extracted data
        Object.assign(candidate, data);
        candidate.processed = true;
        
        return candidate;
    } catch (error) {
        console.error(`Error processing CV ${candidate.filename}:`, error);
        // If there's an error, set a default low score and mark as processed
        candidate.processed = true;
        candidate.error = error.message;
        candidate.score = candidate.score || 0;
        candidate.skills = candidate.skills || [];
        candidate.experience = candidate.experience || 'Unknown';
        candidate.education = candidate.education || 'Unknown';
        candidate.name = candidate.name || 'Unknown Candidate';
        candidate.email = candidate.email || 'no-email@example.com';
        
        return candidate;
    }
}

// Update progress UI
function updateProgressUI(processed, total) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    const percent = Math.min(100, (processed / total) * 100);
    progressBar.style.width = `${percent}%`;
    progressText.textContent = `Processing ${processed}/${total} CVs`;
}

// Display results of CV processing
function displayResults() {
    const candidatesList = document.getElementById('candidates-list');
    candidatesList.innerHTML = '';
    
    appState.candidates.forEach(candidate => {
        const card = document.createElement('div');
        card.className = 'candidate-card';
        
        let matchClass = '';
        if (candidate.score >= 85) matchClass = 'high-match';
        else if (candidate.score >= 75) matchClass = 'medium-match';
        else matchClass = 'low-match';
        
        // If there was an error processing this CV, show it
        let errorMessage = '';
        if (candidate.error) {
            errorMessage = `<div class="error-message"><i class="fas fa-exclamation-circle"></i>${candidate.error}</div>`;
        }
        
        card.innerHTML = `
            <div class="candidate-avatar">${candidate.name ? candidate.name.charAt(0) : '?'}</div>
            <div class="candidate-details">
                <div class="candidate-name">${candidate.name || 'Unknown Candidate'}</div>
                <div>${candidate.experience || 'Unknown'} experience | ${candidate.education || 'Unknown'}</div>
                <div class="candidate-skills">
                    ${(candidate.skills || []).map(skill => `<span class="skill-tag">${skill}</span>`).join('') || 'No skills detected'}
                </div>
                ${errorMessage}
            </div>
            <div class="match-score">
                <div class="score-value ${matchClass}">${candidate.score}%</div>
                <div class="score-label">Match Score</div>
                ${candidate.score >= 80 ? '<div style="color: var(--success); font-size: 12px;">Shortlisted</div>' : ''}
            </div>
        `;
        
        candidatesList.appendChild(card);
    });
    
    document.getElementById('results-container').classList.remove('hidden');
}

// Display shortlisted candidates in Step 4
function displayShortlistedCandidates() {
    const shortlistedList = document.getElementById('shortlisted-list');
    shortlistedList.innerHTML = '';
    
    const shortlisted = appState.shortlistedCandidates;
    
    if (shortlisted.length === 0) {
        shortlistedList.innerHTML = '<p>No candidates met the 80% threshold</p>';
        document.getElementById('send-invites').disabled = true;
        return;
    }
    
    shortlisted.forEach(candidate => {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.style.marginBottom = '10px';
        item.innerHTML = `
            <div class="file-icon">
                <i class="fas fa-user"></i>
            </div>
            <div class="file-name">${candidate.name || 'Unknown Candidate'}</div>
            <div style="color: var(--success);">${candidate.score}% match</div>
        `;
        shortlistedList.appendChild(item);
    });
    
    document.getElementById('send-invites').disabled = false;
}

// Initialize interview slots
function initializeInterviewSlots() {
    const container = document.getElementById('interview-slots-container');
    if (!container) return;
    
    container.innerHTML = ''; // Clear existing slots
    container.classList.remove('hidden');
    
    // Hide preview if it exists
    const previewContainer = document.getElementById('interview-preview');
    if (previewContainer) {
        previewContainer.classList.add('hidden');
    }
    
    // Set min date to today for the start date input
    const startDateInput = document.getElementById('interview-start-date');
    if (startDateInput) {
        const today = new Date().toISOString().split('T')[0];
        startDateInput.min = today;
        startDateInput.value = today;
    }

    // Set a default start time (e.g., 9:00 AM)
    const startTimeInput = document.getElementById('interview-start-time');
    if (startTimeInput) {
        startTimeInput.value = '09:00';
    }

    // Set default duration and break time
    const durationSelect = document.getElementById('interview-duration');
    if (durationSelect) {
        durationSelect.value = '30'; // 30 minutes default
    }

    const breakSelect = document.getElementById('interview-break');
    if (breakSelect) {
        breakSelect.value = '10'; // 10 minutes default
    }

    // Add event listener for modify schedule button
    const modifyButton = document.getElementById('modify-schedule');
    if (modifyButton) {
        modifyButton.addEventListener('click', () => {
            if (previewContainer) previewContainer.classList.add('hidden');
            container.classList.remove('hidden');
        });
    }
}

// Generate interview time slots
function generateInterviewSlots() {
    // Get configuration values
    const startDate = document.getElementById('interview-start-date').value;
    const startTime = document.getElementById('interview-start-time').value;
    const duration = parseInt(document.getElementById('interview-duration').value);
    const breakTime = parseInt(document.getElementById('interview-break').value);
    const interviewMode = document.getElementById('interview-mode').value;
    const location = document.getElementById('interview-location').value;
    const interviewerName = document.getElementById('interviewer-name').value;

    // Validate all required fields
    if (!startDate || !startTime) {
        showNotification('Error', 'Please select both start date and time', 'error');
        return;
    }

    if (!interviewMode || !location) {
        showNotification('Error', 'Please select interview mode and provide location/link', 'error');
        return;
    }

    if (!interviewerName) {
        showNotification('Error', 'Please provide the interviewer\'s name', 'error');
        return;
    }

    // Check if we have shortlisted candidates
    if (!appState.shortlistedCandidates || appState.shortlistedCandidates.length === 0) {
        showNotification('Error', 'No shortlisted candidates available. Please process CVs first.', 'error');
        return;
    }

    console.log('Generating slots for', appState.shortlistedCandidates.length, 'candidates');
    console.log('Start date:', startDate);
    console.log('Start time:', startTime);
    console.log('Duration:', duration);
    console.log('Break time:', breakTime);
    console.log('Interview mode:', interviewMode);
    console.log('Location:', location);
    console.log('Interviewer:', interviewerName);

    // Clear existing slots
    const container = document.getElementById('interview-slots-container');
    container.innerHTML = '';

    try {
        // Calculate time slots
        let currentDateTime = new Date(`${startDate}T${startTime}`);
        const candidates = appState.shortlistedCandidates;

        // Save interview configuration to appState
        appState.interviewConfig = {
            mode: interviewMode,
            location: location,
            interviewer: interviewerName,
            duration: duration,
            breakTime: breakTime
        };

        // Create slots for each candidate
        candidates.forEach((candidate, index) => {
            console.log('Creating slot for candidate:', candidate.name);
            addInterviewSlot(candidate, index, currentDateTime);
            
            // Add duration and break time for next slot
            currentDateTime = new Date(currentDateTime.getTime() + (duration + breakTime) * 60000);
        });

        // Show preview
        showInterviewPreview();
        showNotification('Success', 'Interview slots generated successfully!', 'success');
    } catch (error) {
        console.error('Error generating slots:', error);
        showNotification('Error', 'Failed to generate interview slots: ' + error.message, 'error');
    }
}

// Show interview schedule preview
function showInterviewPreview() {
    const slots = document.querySelectorAll('.interview-slot');
    const previewContent = document.getElementById('preview-content');
    const previewContainer = document.getElementById('interview-preview');
    
    if (!previewContent || !previewContainer || slots.length === 0) {
        showNotification('Error', 'No interview slots to preview', 'error');
        return;
    }

    // Initialize modify schedule button handler
    const modifyButton = document.getElementById('modify-schedule');
    if (modifyButton) {
        modifyButton.onclick = function() {
            document.getElementById('interview-slots-container').classList.remove('hidden');
            previewContainer.classList.add('hidden');
        };
    }

    const scheduleHtml = [];
    const duration = document.getElementById('interview-duration').value;
    const breakTime = document.getElementById('interview-break').value;

    scheduleHtml.push(`
        <div class="preview-header card bg-light mb-3">
            <div class="card-body">
                <h5 class="card-title">Schedule Summary</h5>
                <p class="card-text">
                    <i class="fas fa-clock"></i> ${duration} minutes per interview<br>
                    <i class="fas fa-pause-circle"></i> ${breakTime} minutes break between interviews
                </p>
            </div>
        </div>
    `);

    slots.forEach((slot, index) => {
        const candidateName = slot.querySelector('h4').textContent;
        const date = slot.querySelector('.interview-date').value;
        const time = slot.querySelector('.interview-time').value;
        const mode = slot.querySelector('.interview-mode').value;

        try {
            const formattedDate = new Date(date).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            const formattedTime = new Date(`${date}T${time}`).toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            });

            const endTime = new Date(`${date}T${time}`);
            endTime.setMinutes(endTime.getMinutes() + parseInt(duration));
            const formattedEndTime = endTime.toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            });

            scheduleHtml.push(`
                <div class="preview-slot card mb-3 ${index % 2 === 0 ? 'bg-white' : 'bg-light'}">
                    <div class="card-body">
                        <div class="preview-candidate mb-2">
                            <h5 class="mb-0">
                                <i class="fas fa-user"></i> ${candidateName}
                            </h5>
                        </div>
                        <div class="preview-datetime mb-2">
                            <i class="fas fa-calendar"></i> ${formattedDate}<br>
                            <i class="fas fa-clock"></i> ${formattedTime} - ${formattedEndTime}
                        </div>
                        <div class="preview-mode">
                            <i class="fas ${mode === 'virtual' ? 'fa-video' : mode === 'phone' ? 'fa-phone' : 'fa-building'}"></i>
                            ${mode.charAt(0).toUpperCase() + mode.slice(1)} Interview
                        </div>
                    </div>
                </div>
            `);
        } catch (error) {
            console.error('Error formatting date/time for preview:', error);
            showNotification('Error', 'Invalid date or time format', 'error');
            return;
        }
    });

    previewContent.innerHTML = scheduleHtml.join('\n');
    document.getElementById('interview-slots-container').classList.add('hidden');
    previewContainer.classList.remove('hidden');
}

// Send interview invitations to shortlisted candidates
async function sendInterviewInvites() {
    const slots = document.querySelectorAll('.interview-slot');
    
    if (!slots || slots.length === 0) {
        showNotification('Error', 'No interview slots found. Please generate slots first.', 'error');
        return;
    }

    if (!appState.jobDescription) {
        showNotification('Error', 'Job description is missing. Please start from the beginning.', 'error');
        return;
    }

    const interviewData = {
        candidates: [],
        job_description: appState.jobDescription,
        schedule_config: {
            duration: parseInt(document.getElementById('interview-duration').value),
            break_time: parseInt(document.getElementById('interview-break').value)
        }
    };
    
    // Validate and collect data for each candidate
    for (const slot of slots) {
        const date = slot.querySelector('.interview-date').value;
        const time = slot.querySelector('.interview-time').value;
        const mode = slot.querySelector('.interview-mode').value;
        const location = slot.querySelector('.interview-location').value;
        const interviewer = slot.querySelector('.interviewer-name').value;
        
        if (!date || !time || !mode || !location || !interviewer) {
            showNotification('Error', 'Please fill in all interview details (date, time, mode, location, and interviewer)', 'error');
            return;
        }

        // Get candidate info - either from shortlisted candidates or from manual input
        let candidateInfo;
        const candidateId = slot.dataset.candidateId;
        
        if (candidateId !== undefined && candidateId !== null) {
            // Get from shortlisted candidates
            const candidate = appState.shortlistedCandidates[parseInt(candidateId)];
            candidateInfo = {
                name: candidate.name,
                email: candidate.email,
                score: candidate.score,
                strengths: candidate.strengths || [],
                weaknesses: candidate.weaknesses || []
            };
        } else {
            // Get from manual input
            const nameInput = slot.querySelector('.candidate-name');
            const emailInput = slot.querySelector('.candidate-email');
            
            if (!nameInput.value || !emailInput.value) {
                showNotification('Error', 'Please fill in candidate name and email for all additional slots', 'error');
                return;
            }
            
            candidateInfo = {
                name: nameInput.value,
                email: emailInput.value,
                score: null,
                strengths: [],
                weaknesses: []
            };
        }
        
        interviewData.candidates.push({
            ...candidateInfo,
            interviewDetails: {
                date,
                time,
                mode,
                location,
                interviewer
            }
        });
    }
    
    try {
        showLoading(true, "Sending interview invitations...");
        
        // Send to backend
        const response = await fetch('/api/schedule-interviews', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(interviewData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to schedule interviews');
        }
        
        const responseData = await response.json();
        
        // Show success
        document.getElementById('step4-content').classList.add('hidden');
        
        // Update success message with details
        const successContent = document.getElementById('success-content');
        const emailPreviewsEl = document.createElement('div');
        emailPreviewsEl.className = 'email-previews card';
        
        // Add heading for email previews if there are any
        if (responseData.email_previews && responseData.email_previews.length > 0) {
            emailPreviewsEl.innerHTML = `
                <div class="card-header">
                    <h3 class="mb-0">Email Previews</h3>
                </div>
                <div class="card-body">
                    ${responseData.email_previews.map(preview => `
                        <div class="email-preview mb-4">
                            <div class="preview-header">
                                <div class="mb-2">
                                    <strong>To:</strong> ${preview.candidate} &lt;${preview.email}&gt;
                                </div>
                                <div>
                                    <strong>Subject:</strong> ${preview.subject}
                                </div>
                            </div>
                            <div class="preview-content mt-3">
                                <div class="email-body">
                                    ${Array.isArray(preview.preview) ? preview.preview.join('<br>') : preview.preview}
                                </div>
                            </div>
                        </div>
                        ${preview !== responseData.email_previews[responseData.email_previews.length - 1] ? '<hr>' : ''}
                    `).join('')}
                </div>
            `;
            
            // Insert before the restart button
            const restartBtn = successContent.querySelector('#restart-process');
            successContent.querySelector('.success-message').insertBefore(
                emailPreviewsEl, 
                restartBtn
            );
        }
        
        successContent.classList.remove('hidden');
        
        showNotification('Success', `Interview invitations sent to ${responseData.scheduled} candidates!`, 'success');
    } catch (error) {
        console.error('Error scheduling interviews:', error);
        showNotification('Error', error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Navigate between workflow steps
function navigateToStep(stepIndex) {
    appState.currentStep = stepIndex;
    
    stepIndicators.forEach((indicator, index) => {
        if (index < stepIndex - 1) {
            indicator.classList.add('completed');
            indicator.classList.remove('active');
        } else if (index === stepIndex - 1) {
            indicator.classList.add('active');
            indicator.classList.remove('completed');
        } else {
            indicator.classList.remove('active', 'completed');
        }
    });
    
    stepContents.forEach((content, index) => {
        content.classList.remove('active');
        if (index === stepIndex - 1) {
            content.classList.add('active');
        }
    });
}

// Reset process to start over
function resetProcess() {
    // Reset app state
    appState.jobDescription = null;
    appState.candidates = [];
    appState.shortlistedCandidates = [];
    appState.currentStep = 1;
    
    // Reset UI
    document.getElementById('jd-filename').textContent = '';
    document.getElementById('jd-preview').classList.add('hidden');
    document.getElementById('jd-position').textContent = 'Loading...';
    document.getElementById('jd-requirements').innerHTML = '<li>Loading requirements...</li>';
    
    document.getElementById('cv-file-list').innerHTML = '';
    document.getElementById('cv-preview').classList.add('hidden');
    
    document.getElementById('progress-bar').style.width = '0%';
    document.getElementById('progress-text').textContent = 'Processing 0/0 CVs';
    document.getElementById('candidates-list').innerHTML = '';
    document.getElementById('shortlisted-list').innerHTML = '';
    
    document.getElementById('interview-date').value = '';
    document.getElementById('interview-time').value = '';
    
    // Reset success content
    const successContent = document.getElementById('success-content');
    successContent.classList.add('hidden');
    
    // Remove any existing email previews
    const emailPreviews = successContent.querySelector('.email-previews');
    if (emailPreviews) {
        emailPreviews.remove();
    }
    
    // Navigate to step 1
    navigateToStep(1);
}

// Format file size in readable format
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Add a new interview slot
function addInterviewSlot(candidate = null, index = null, datetime = null) {
    const container = document.getElementById('interview-slots-container');
    const slotCount = container.querySelectorAll('.interview-slot').length;
    
    let date = '';
    let time = '';
    if (datetime) {
        const dt = new Date(datetime);
        date = dt.toISOString().split('T')[0];
        time = dt.toTimeString().split(' ')[0].substring(0, 5);
    }

    // Get interview configuration
    const config = appState.interviewConfig || {};
    const mode = config.mode || 'virtual';
    const location = config.location || '';
    const interviewer = config.interviewer || '';
    
    const slotHtml = `
        <div class="interview-slot card mb-3" data-slot-id="${slotCount}" ${index !== null ? `data-candidate-id="${index}"` : ''}>
            <div class="card-body">
                <div class="slot-header">
                    <h4 class="mb-3">${candidate ? candidate.name : 'Additional Interview Slot'}</h4>
                    ${candidate ? '' : `
                    <div class="form-group">
                        <label>Candidate Name</label>
                        <input type="text" class="candidate-name form-control" required>
                    </div>
                    <div class="form-group">
                        <label>Candidate Email</label>
                        <input type="email" class="candidate-email form-control" required>
                    </div>
                    `}
                </div>
                <div class="form-row">
                    <div class="form-group col-md-4">
                        <label>Interview Date</label>
                        <input type="date" class="interview-date form-control" value="${date}" required>
                    </div>
                    <div class="form-group col-md-4">
                        <label>Interview Time</label>
                        <input type="time" class="interview-time form-control" value="${time}" required>
                    </div>
                    <div class="form-group col-md-4">
                        <label>Interview Mode</label>
                        <select class="interview-mode form-control" required>
                            <option value="virtual" ${mode === 'virtual' ? 'selected' : ''}>Virtual (Zoom)</option>
                            <option value="in-person" ${mode === 'in-person' ? 'selected' : ''}>In-Person</option>
                            <option value="phone" ${mode === 'phone' ? 'selected' : ''}>Phone Call</option>
                        </select>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group col-md-6">
                        <label>Location/Link</label>
                        <input type="text" class="interview-location form-control" value="${location}" placeholder="Office address or meeting link" required>
                    </div>
                    <div class="form-group col-md-6">
                        <label>Interviewer</label>
                        <input type="text" class="interviewer-name form-control" value="${interviewer}" placeholder="Who will conduct the interview?" required>
                    </div>
                </div>
                ${candidate ? '' : `
                <button type="button" class="btn btn-danger remove-slot mt-2">
                    <i class="fas fa-trash"></i> Remove Slot
                </button>
                `}
            </div>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', slotHtml);

    // Set min date to today for the new date input
    const newSlot = container.lastElementChild;
    const dateInput = newSlot.querySelector('.interview-date');
    if (dateInput && !datetime) {
        dateInput.min = new Date().toISOString().split('T')[0];
    }

    // Add event listener for remove button if it exists
    const removeButton = newSlot.querySelector('.remove-slot');
    if (removeButton) {
        removeButton.addEventListener('click', () => {
            newSlot.remove();
        });
    }

    return newSlot;
}

// Show/hide loading indicator
function showLoading(show, message = 'Processing...') {
    const loadingEls = document.querySelectorAll('.loading');
    
    loadingEls.forEach(el => {
        el.style.display = show ? 'block' : 'none';
        
        // Update message if provided
        const messageEl = el.querySelector('p');
        if (messageEl && message) {
            messageEl.textContent = message;
        }
    });
}

// Show notification
function showNotification(title, message, type = 'success') {
    const notification = document.getElementById('notification');
    
    // Set content
    notification.querySelector('.notification-title').textContent = title;
    notification.querySelector('.notification-message').textContent = message;
    
    // Set type
    notification.className = 'notification';
    notification.classList.add(`notification-${type}`);
    
    // Set icon
    let iconClass = 'fa-info-circle';
    if (type === 'success') iconClass = 'fa-check-circle';
    if (type === 'error') iconClass = 'fa-exclamation-circle';
    
    notification.querySelector('.notification-icon i').className = `fas ${iconClass}`;
    
    // Show notification
    notification.classList.add('show');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
    }, 5000);
}
