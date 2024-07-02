document.addEventListener('DOMContentLoaded', function() {
    var searchButton = document.getElementById('search-button');
    var searchInput = document.getElementById('search-input');
    var searchResultsContainer = document.getElementById('search-results');
    var reportButton = document.getElementById('report-button');

    // URL 파라미터에서 검색어를 가져와서 검색창에 채움
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('url');
    if (query) {
        searchInput.value = decodeURIComponent(query);
        performSearch(query); // 페이지 로드 시 검색어가 있으면 검색 실행
    }

    function performSearch(searchTerm) {
        // Clear previous results
        searchResultsContainer.innerHTML = '';

        // Django 뷰로부터 데이터를 가져옴
        fetch(`/classify/get_search_results/?url=${searchTerm}`)
            .then(response => response.json())
            .then(data => {
                const result = `"${data.url}" | (${data.classification}) | (${data.keywords.join(', ')}) | (신고 후 차단)`;
                const resultElement = document.createElement('div');
                resultElement.textContent = result;
                resultElement.className = 'search-result';
                searchResultsContainer.appendChild(resultElement);
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }

    searchButton.addEventListener('mousedown', function() {
        this.style.backgroundColor = '#666'; // 버튼을 누르고 있을 때 색상
    });

    searchButton.addEventListener('mouseup', function() {
        this.style.backgroundColor = '#0033cc'; // 버튼에서 손을 뗐을 때 원래 색상
    });

    searchButton.addEventListener('mouseleave', function() {
        this.style.backgroundColor = '#0033cc'; // 버튼 밖으로 커서가 나갔을 때 원래 색상
    });

    searchButton.addEventListener('click', function(event) {
        event.preventDefault(); // 폼 제출을 막음
        const searchTerm = searchInput.value;
        const url = new URL(window.location);
        url.searchParams.set('url', searchTerm);
        window.history.pushState({}, '', url);
        performSearch(searchTerm);
    });

    searchInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault(); // 폼 제출을 막음
            const searchTerm = searchInput.value;
            const url = new URL(window.location);
            url.searchParams.set('url', searchTerm);
            window.history.pushState({}, '', url);
            performSearch(searchTerm);
        }
    });

    reportButton.addEventListener('click', function() {
        window.location.href = 'reportPage.html';
    });
});
