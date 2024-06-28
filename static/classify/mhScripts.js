document.addEventListener('DOMContentLoaded', function() {
    var searchButton = document.getElementById('search-button');
    var searchInput = document.getElementById('search-input');

    // 버튼 스타일링 이벤트
    searchButton.addEventListener('mousedown', function() {
        this.style.backgroundColor = '#666'; // 버튼을 누르고 있을 때 색상
    });

    searchButton.addEventListener('mouseup', function() {
        this.style.backgroundColor = '#0033cc'; // 버튼에서 손을 뗐을 때 원래 색상
    });

    searchButton.addEventListener('mouseleave', function() {
        this.style.backgroundColor = '#0033cc'; // 버튼 밖으로 커서가 나갔을 때 원래 색상
    });

    // 페이지 이동 이벤트
    function navigateToSearchPage() {
        const query = searchInput.value;
        if (query) {
            window.location.href = `searchPage.html?query=${encodeURIComponent(query)}`;
        } else {
            window.location.href = 'searchPage.html';
        }
    }

    searchButton.addEventListener('click', navigateToSearchPage);

    searchInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            navigateToSearchPage();
        }
    });
});