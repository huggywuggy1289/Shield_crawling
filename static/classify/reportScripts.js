document.addEventListener('DOMContentLoaded', function() {
    const reportTagSelect = document.getElementById('report-tag');
    const otherTagInput = document.getElementById('other-tag');

    reportTagSelect.addEventListener('change', function() { // report-tag 셀렉트 박스의 값이 변경될 때 발생하는 이벤트 리스너
        if (this.value === '기타') {  // 만약 선택된 값이 '기타'라면 other-tag 입력 필드를 보이게 하고, 필수 입력 필드로 설정
            otherTagInput.style.display = 'block';
            otherTagInput.required = true;
        } else {
            otherTagInput.style.display = 'none';// 그렇지 않은 경우에는 숨기고 필수 입력을 해제
            otherTagInput.required = false;
            otherTagInput.value = '';
        }
    });

//    document.getElementById('report-form').addEventListener('submit', function(event) {
//        event.preventDefault();
//        alert("신고가 접수되었습니다. 감사합니다!");
//
//        // 수동으로 폼 데이터 생성 // 사용자가 입력한 URL (reported-url)과 신고 이유 (report-reason)를 FormData 객체에 추가
//        const formData = new FormData();
//        formData.append('reported-url', document.getElementById('reported-url').value);
//        formData.append('report-reason', document.getElementById('report-reason').value);
//
//        // 신고 태그 처리
//        const selectedTag = reportTagSelect.value;
//        if (selectedTag === '기타') {
//            const otherTagValue = otherTagInput.value.trim();  // 사용자가 입력한 값을 가져옴
//            formData.append('report-tag', otherTagValue);  // 기타일 경우 사용자가 입력한 값을 신고 태그로 설정
//        } else {
//            formData.append('report-tag', selectedTag);  // 기타가 아닌 경우 선택된 신고 태그를 설정
//        }

        // fetch API를 사용하여 서버로 전송할 수 있음
        // fetch('url', {
        //     method: 'POST',
        //     body: formData
        // }).then(response => {
        //     // 처리 후 작업
        // }).catch(error => {
        //     console.error('Error:', error);
        // });
    });
});