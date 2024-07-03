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
