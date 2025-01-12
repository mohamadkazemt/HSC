$(document).ready(function () {
    // کلیک روی زنگوله برای دریافت اعلان‌ها
    $("#notification-bell").click(function () {
        $.ajax({
            url: "/dashboard/notifications/",
            type: "GET",
            success: function (data) {
                $("#kt_drawer_chat_messenger_body").html(data);
            },
            error: function (xhr, status, error) {
                console.error("Failed to fetch notifications:", error);
            }
        });
    });
});
