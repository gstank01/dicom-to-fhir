async function fetchPatient() {
    const identifier = document.getElementById('patientId').value;
    const patientCard = document.getElementById('patientCard');
    const loading = document.getElementById('loading');
    const errorDiv = document.getElementById('error');

    // Reset UI states before starting a new search
    patientCard.classList.add('hidden');
    errorDiv.classList.add('hidden');
    loading.classList.remove('hidden');

    try {
        // Call the Python Vercel backend handler
        const response = await fetch('/api/fhir_auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ identifier: identifier })
        });

        const data = await response.json();

        if (!data.success) throw new Error(data.error || "Lookup failed");

        // The Python backend returns the patientBundle in the JSON response
        const patient = data.patientBundle.entry[0].resource;

        // Parse FHIR fields (with safe fallbacks in case data is missing)
        const name = patient.name ? `${patient.name[0].given.join(' ')} ${patient.name[0].family}` : 'N/A';
        const dob = patient.birthDate || 'N/A';
        const mrn = identifier; // Using the identifier passed to the backend
        
        let address = 'N/A';
        if (patient.address && patient.address.length > 0) {
            const addr = patient.address[0];
            address = `${addr.line ? addr.line.join(', ') : ''}, ${addr.city || ''}, ${addr.state || ''}`;
            postcode = addr.postalCode || 'N/A';
        }

        // Update the HTML text elements
        document.getElementById('p-name').innerText = name;
        document.getElementById('p-dob').innerText = dob;
        document.getElementById('p-mrn').innerText = mrn;
        document.getElementById('p-address').innerText = address;
        document.getElementById('p-postcode').innerText = postcode;


        // Reveal the updated patient card
        loading.classList.add('hidden');
        patientCard.classList.remove('hidden');

    } catch (err) {
        // Handle network errors or backend failures gracefully
        loading.classList.add('hidden');
        errorDiv.innerText = err.message;
        errorDiv.classList.remove('hidden');
    }
}