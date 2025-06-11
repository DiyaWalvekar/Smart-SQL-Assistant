lucide.createIcons();

    const dropZone = document.getElementById('dropZone');
    const loadingIndicator = document.getElementById('loadingSkeleton');
    const sqlOutput = document.getElementById('sqlOutput');
    const closeFullscreenBtn = document.getElementById('closeFullscreenBtn');

    function allowDrop(e) { e.preventDefault(); }
    function handleDrop(e) {
      e.preventDefault();
      dropZone.classList.remove('dragover');
      document.getElementById('fileInput').files = e.dataTransfer.files;
    }
    function addDropHover() { dropZone.classList.add('dragover'); }
    function removeDropHover() { dropZone.classList.remove('dragover'); }

    // Upload form
    document.getElementById('uploadForm').onsubmit = function(e) {
      e.preventDefault();
      const file = document.getElementById('fileInput').files[0];
      if (!file) return alert("Please select a file first!");
      const formData = new FormData();
      formData.append("file", file);
      fetch('/upload', { method:'POST', body: formData })
        .then(r => r.json())
        .then(data => {
          document.getElementById('uploadMessage').innerHTML = data.error
            ? `<span class="text-red-600">❌ ${data.error}</span>`
            : `<span class="text-green-700">✅ File uploaded: <strong>${data.table}</strong></span>`;
        })
        .catch(err => {
          document.getElementById('uploadMessage').innerHTML = `<span class="text-red-600">❌ ${err}</span>`;
        });
    };

    // Query button
    document.getElementById('submitQueryBtn').onclick = function() {
      const queryText = document.getElementById('queryText').value.trim();
      if (!queryText) return alert("Please enter a query!");
      loadingIndicator.classList.remove('hidden');
      sqlOutput.classList.add('hidden');
      fetch('/query', {
        method: 'POST',
        body: new URLSearchParams({ mode:'text', text:queryText })
      })
      .then(r => r.json())
      .then(data => {
        loadingIndicator.classList.add('hidden');
        if (data.error) {
          document.getElementById('errorMessage').textContent = data.error;
          return;
        }
        document.getElementById('errorMessage').textContent = '';
        sqlOutput.classList.remove('hidden');
        sqlOutput.classList.add('fullscreen');
        closeFullscreenBtn.classList.remove('hidden');
        loadQueryHistory();
        document.getElementById('tableResult').innerHTML = data.table || '';
        document.getElementById('chartResult').innerHTML = data.chart_image
          ? `<img src="${data.chart_image}" class="w-full rounded-lg border border-green-300 shadow" />` : '';
        document.getElementById('insightsResult').innerHTML = data.insights || '';
      })
      .catch(err => {
        loadingIndicator.classList.add('hidden');
        document.getElementById('errorMessage').textContent = "Error: " + err;
      });
    };

    // Voice recognition
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (Recognition) {
      const recog = new Recognition();
      recog.lang = 'en-US'; recog.interimResults = true;
      let listening = false;
      document.getElementById('voiceQueryBtn').onclick = () => {
        if (listening) { recog.stop(); } else { recog.start(); }
        listening = !listening;
      };
      recog.onresult = e => {
        document.getElementById('queryText').value = e.results[0][0].transcript;
      };
      recog.onerror = e => alert("Voice error: " + e.error);
    } else {
      document.getElementById('voiceQueryBtn').disabled = true;
    }

    function closeFullscreen() {
      sqlOutput.classList.remove('fullscreen');
      closeFullscreenBtn.classList.add('hidden');
    }

    function downloadCSV() {
      const tbl = document.getElementById("tableResult").querySelector("table");
      if (!tbl) return alert("No table to export!");
      let csv="";
      for (let row of tbl.rows) {
        csv += Array.from(row.cells).map(c=>`"${c.innerText}"`).join(",") + "\n";
      }
      const a=document.createElement('a');
      a.href=URL.createObjectURL(new Blob([csv],{type:"text/csv"}));
      a.download="query_result.csv"; a.click();
    }

    function loadQueryHistory() {
  fetch('/get_history')
    .then(response => response.json())
    .then(data => {
      const historyDiv = document.getElementById('history');
      historyDiv.innerHTML = '<h3 class="text-lg font-semibold mb-2">Query History</h3>';
      data.forEach(item => {
        historyDiv.innerHTML += `<p class="bg-gray-100 p-2 rounded mb-1">${item.timestamp} - ${item.query}</p>`;
      });
    });
}


    // Auto-suggestions
    document.getElementById('queryText').addEventListener('input', function() {
      const txt = this.value.trim();
      if (!txt) return document.getElementById('suggestionsBox').innerText = '';
      fetch('/suggest', {
        method:'POST',
        headers:{'Content-Type':'application/x-www-form-urlencoded'},
        body:new URLSearchParams({query: txt})
      })
      .then(r => r.json())
      .then(d => {
        document.getElementById('suggestionsBox').innerText =
          `Intent: ${d.intent} — Suggestions: ${d.expansion.join(', ')}`;
      })
      .catch(console.error);
    });
  