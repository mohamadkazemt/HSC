(function () {
    "use strict";

    function getCookie(name) {
        const cookie = document.cookie
            .split(";")
            .map((item) => item.trim())
            .find((item) => item.startsWith(name + "="));
        return cookie ? decodeURIComponent(cookie.split("=").slice(1).join("=")) : "";
    }

    function askPassword(moduleTitle) {
        return new Promise((resolve) => {
            const dialog = document.createElement("dialog");
            dialog.dir = "rtl";
            dialog.style.cssText = "border:0;border-radius:10px;padding:0;box-shadow:0 15px 45px #0005;max-width:420px;width:calc(100% - 32px)";
            dialog.innerHTML = `
                <form method="dialog" style="padding:22px">
                    <h2 style="margin:0 0 12px;font-size:18px">فعال‌سازی ماژول</h2>
                    <p style="margin:0 0 14px">برای فعال‌سازی «${moduleTitle}»، رمز عبور حساب مدیر را وارد کنید.</p>
                    <input type="password" autocomplete="current-password" required
                           style="box-sizing:border-box;width:100%;padding:9px;border:1px solid #aaa;border-radius:6px">
                    <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
                        <button value="cancel">انصراف</button>
                        <button value="confirm" class="button default">فعال‌سازی</button>
                    </div>
                </form>`;
            document.body.appendChild(dialog);
            const input = dialog.querySelector("input");
            dialog.addEventListener("close", () => {
                const password = dialog.returnValue === "confirm" ? input.value : null;
                dialog.remove();
                resolve(password);
            }, {once: true});
            dialog.showModal();
            input.focus();
        });
    }

    async function changeModuleStatus(checkbox) {
        const requestedActive = checkbox.checked;
        let password = "";

        if (requestedActive) {
            password = await askPassword(checkbox.dataset.moduleTitle);
            if (password === null || password === "") {
                checkbox.checked = false;
                return;
            }
        }

        checkbox.disabled = true;
        const body = new FormData();
        body.append("is_active", requestedActive ? "true" : "false");
        body.append("activation_password", password);

        try {
            const response = await fetch(checkbox.dataset.toggleUrl, {
                method: "POST",
                headers: {"X-CSRFToken": getCookie("csrftoken")},
                body: body,
                credentials: "same-origin",
            });
            const data = await response.json();
            if (!response.ok || !data.ok) {
                throw new Error(data.message || "تغییر وضعیت ماژول انجام نشد.");
            }
            checkbox.checked = data.is_active;
            window.location.reload();
        } catch (error) {
            checkbox.checked = !requestedActive;
            checkbox.disabled = false;
            window.alert(error.message);
        }
    }

    document.addEventListener("change", function (event) {
        if (event.target.classList.contains("module-status-toggle")) {
            changeModuleStatus(event.target);
        }
    });
})();
