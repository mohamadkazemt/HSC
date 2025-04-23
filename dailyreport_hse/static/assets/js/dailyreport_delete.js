function deleteReport(reportId) {
    Swal.fire({
        title: 'آیا مطمئن هستید؟',
        text: "این عملیات قابل بازگشت نیست!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'بله، حذف شود',
        cancelButtonText: 'انصراف'
    }).then((result) => {
        if (result.isConfirmed) {
            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            fetch(`/dailyreport_hse/report/${reportId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const row = document.querySelector(`tr[data-report-id="${reportId}"]`);
                    if (row) {
                        row.remove();
                        Swal.fire({
                            title: 'حذف شد!',
                            text: data.message,
                            icon: 'success',
                            confirmButtonText: 'باشه'
                        });
                    }
                } else {
                    Swal.fire({
                        title: 'خطا!',
                        text: data.message || 'خطا در حذف گزارش',
                        icon: 'error',
                        confirmButtonText: 'باشه'
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({
                    title: 'خطا!',
                    text: 'خطا در ارتباط با سرور',
                    icon: 'error',
                    confirmButtonText: 'باشه'
                });
            });
        }
    });
}