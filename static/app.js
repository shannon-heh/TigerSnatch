const toastAdded = $(
    $.parseHTML(`
<div
    id="toast-added"
    class="toast align-items-center text-white bg-success border-0"
    role="alert"
    aria-live="assertive"
    aria-atomic="true"
    data-bs-delay="3000"
>
    <div class="d-flex">
        <div class="toast-body">Successfully added to waitlist!</div>
        <button
            type="button"
            class="btn-close btn-close-white me-2 m-auto"
            data-bs-dismiss="toast"
            aria-label="Close"
        ></button>
    </div>
</div>
`)
);

const toastRemoved = $(
    $.parseHTML(`
<div
    id="toast-removed"
    class="toast align-items-center text-white bg-warning border-0"
    role="alert"
    aria-live="assertive"
    aria-atomic="true"
    data-bs-delay="3000"
>
    <div class="d-flex">
        <div class="toast-body">Successfully removed from waitlist!</div>
        <button
            type="button"
            class="btn-close btn-close-white me-2 m-auto"
            data-bs-dismiss="toast"
            aria-label="Close"
        ></button>
    </div>
</div>
`)
);

const toastUserDoesNotExist = $(
    $.parseHTML(`
<div
    id="toast-user-does-not-exist"
    class="toast align-items-center text-white bg-danger border-0"
    role="alert"
    aria-live="assertive"
    aria-atomic="true"
    data-bs-delay="3000"
>
    <div class="d-flex">
        <div class="toast-body">That netID does not exist.</div>
        <button
            type="button"
            class="btn-close btn-close-white me-2 m-auto"
            data-bs-dismiss="toast"
            aria-label="Close"
        ></button>
    </div>
</div>
`)
);

const toastEmailsOn = $(
    $.parseHTML(`
<div
    id="toast-emails-on"
    class="toast align-items-center text-white bg-success border-0"
    role="alert"
    aria-live="assertive"
    aria-atomic="true"
    data-bs-delay="3000"
>
    <div class="d-flex">
        <div class="toast-body">Email notifications turned on! Reloading in a few seconds...</div>
        <button
            type="button"
            class="btn-close btn-close-white me-2 m-auto"
            data-bs-dismiss="toast"
            aria-label="Close"
        ></button>
    </div>
</div>
`)
);

const toastEmailsOff = $(
    $.parseHTML(`
<div
    id="toast-emails-off"
    class="toast align-items-center text-white bg-success border-0"
    role="alert"
    aria-live="assertive"
    aria-atomic="true"
    data-bs-delay="3000"
>
    <div class="d-flex">
        <div class="toast-body">Email notifications turned off! Reloading in a few seconds...</div>
        <button
            type="button"
            class="btn-close btn-close-white me-2 m-auto"
            data-bs-dismiss="toast"
            aria-label="Close"
        ></button>
    </div>
</div>
`)
);

// When user clicks on "Contact" for a particular match,
// new tab should open with the link specified in "tradeEmailLink"
// Fill in placeholders (in ALL CAPS) to craft email using String.replace()
// e.g. tradeEmailSubject.replace('MATCH_SECTION', 'P01')
// Let me know if spaces & line breaks dont work
const tradeEmailSubject = "TigerSnatch: Trade Sections for MATCH_SECTION?";
const tradeEmailBody = `
Hi MATCH_NETID, 

From TigerSnatch, I saw that you're enrolled in COURSE_NAME MATCH_SECTION. I'm currently in MY_SECTION. 
Would you like to set up a time to trade sections with me?

Thank you,
MY_NETID
`;
const tradeEmailLink = `https://mail.google.com/mail/u/0/?fs=1&to=MATCH_NETID@princeton.edu&su=${tradeEmailSubject}?&body=${tradeEmailBody}`;

// scrolls to the bottom of id #dest
let scrollBottom = function (dest) {
    $(dest).animate(
        {
            scrollTop: $(dest)[0].scrollHeight - $(dest)[0].clientHeight,
        },
        500
    );
};

// scrolls to the top of id #dest
let resetScroll = function (dest) {
    $(dest).animate(
        {
            scrollTop: 0,
        },
        500
    );
};

// listens for submission of search form
let searchFormListener = function () {
    $("form#search-form").on("submit", function (e) {
        e.preventDefault();

        // automatically close the keyboard on iOS
        $("#search-form-input").blur();

        // close the tooltip if open
        $("#search-form-input").tooltip("hide");

        // get serach query
        query = encodeURIComponent($("#search-form-input").prop("value"));

        // construct new URL
        params = location.search;
        curr_path = location.pathname;
        if (params === "") {
            curr_path = curr_path + "?query=" + query;
        } else {
            curr_path = curr_path + "?";
            params = params.replace("?", "");
            arr = params.split("&");
            for (let i = 0; i < arr.length; i++) {
                if (i > 0) curr_path += "&";
                if (arr[i].startsWith("query")) curr_path = curr_path + "query=" + query;
                else curr_path += arr[i];
            }
        }
        // get search results
        if (query.trim() === "") {
            endpoint = "/searchresults";
        } else {
            endpoint = `/searchresults/${query}`;
        }
        $.post(endpoint, function (res) {
            $("div#search-results").html(res);
            window.history.pushState(
                { restore: "search", html: res },
                "restore search results",
                curr_path
            );
            // adds listener to new search results
            searchResultListener();
            resetScroll("#search-results");
            dashboardSkip();
        });
    });
};

// listens for selection of search result
let searchResultListener = function () {
    $(".search-results-link").on("click", function (e) {
        e.preventDefault();

        // blur frame while loading
        $("*").css("pointer-events", "none");
        $("*").css("cursor", "wait");
        $("#right-wrapper").css("filter", "blur(2px)");

        // remove gray background from currently selected course entry
        $("a.selected-course").css("background-color", "");
        $("a.selected-course").removeClass("selected-course");

        closest_a = $(this).closest("a");

        // background: #C0BDBD;
        // add gray background to selected course
        closest_a.css("background-color", "#ffe58a");
        closest_a.addClass("selected-course");

        course_link = closest_a.attr("href");
        courseid = closest_a.attr("data-courseid");

        scrollBottom("#main");

        // get course information
        $.post(`/courseinfo/${courseid}`, function (res) {
            // change search form to /course endpoint
            $("form#search-form").attr("action", "/course");
            $("input#search-form-courseid").attr("value", courseid);
            $("#right-wrapper").html(res);

            // unblur frame
            $("#right-wrapper").css("filter", "");
            $("*").css("cursor", "");
            $("*").css("pointer-events", "");

            // update URL
            window.history.pushState({ restore: "right", html: res }, "", course_link);

            // add listener to new switches & modals, and re-initialize
            // all tooltips and toasts
            switchListener();
            initTooltipsToasts();
            showAllListener();
            modalCancelListener();
            modalConfirmListener();
            searchSkip();
        });
    });
};

// listens for when user clicks on course in dashboard
// to navigate to its course page
let dashboardCourseSelectListener = function () {
    $(".dashboard-course-link").on("click", function (e) {
        // blur frame while loadidng
        $("*").css("pointer-events", "none");
        $("#right-wrapper").css("filter", "blur(2px)");
    });
};

i = 0; // dummy variable used for toast ids

// listens for toggle of waitlist notification switch
let switchListener = function () {
    $("input.waitlist-switch").change(function (e) {
        e.preventDefault();
        classid = e.target.getAttribute("data-classid");

        $("#confirm-remove-waitlist").attr("data-classid", classid);
        $("#close-waitlist-modal").attr("data-classid", classid);

        switchid = `#switch-${classid}`;

        // if user is not on waitlist for this class, then add them
        if (!$(switchid).attr("checked")) {
            $(switchid).attr("disabled", true);
            $.post(`/add_to_waitlist/${classid}`, function (res) {
                // checks that user successfully added to waitlist on back-end
                if (res["isSuccess"] === 2) {
                    $(switchid).attr("disabled", false);
                    return;
                }
                if (res["isSuccess"] === 0) {
                    $("#close-waitlist-modal").modal("show");
                    $(switchid).attr("checked", false);
                    $(switchid).prop("checked", false);
                    $(switchid).attr("disabled", false);
                    return;
                }
                $(switchid).attr("checked", true);
                $(switchid).attr("data-bs-toggle", "modal");
                $(switchid).attr("data-bs-target", "#confirm-remove-waitlist");
                $(switchid).attr("disabled", false);

                $(".toast-container").prepend(toastAdded.clone().attr("id", "toast-added-" + ++i));
                $("#toast-added-" + i).toast("show");
            });
        }
    });
};

// listens for "Confirm" removal from waitlist
let modalConfirmListener = function () {
    $("#waitlist-modal-confirm").on("click", function (e) {
        e.preventDefault();
        classid = $("#confirm-remove-waitlist").attr("data-classid");
        switchid = `#switch-${classid}`;
        $(switchid).attr("disabled", true);
        $.post(`/remove_from_waitlist/${classid}`, function (res) {
            // checks that user successfully removed from waitlist on back-end
            if (!res["isSuccess"]) {
                $(switchid).attr("disabled", false);
                return;
            }
            $(`${switchid}.dashboard-switch`).closest("tr.dashboard-course-row").remove();
            $(switchid).removeAttr("checked");
            $(switchid).removeAttr("data-bs-toggle");
            $(switchid).removeAttr("data-bs-target");
            $(switchid).attr("disabled", false);

            $(".toast-container").prepend(toastRemoved.clone().attr("id", "toast-removed-" + ++i));
            $("#toast-removed-" + i).toast("show");
        });
    });
};

// listens for "Cancel" removal from waitlist
let modalCancelListener = function () {
    $("#waitlist-modal-cancel").on("click", function (e) {
        e.preventDefault();
        classid = $("#confirm-remove-waitlist").attr("data-classid");
        $(`#switch-${classid}`).prop("checked", true);
    });
};

let showAllListener = function () {
    $("#show-all-check").on("click", function (e) {
        if ($(this).prop("checked")) {
            $(".available-section-row").removeClass("d-none");
            $("#no-full-message").addClass("d-none");
        } else {
            $(".available-section-row").addClass("d-none");
            $("#no-full-message").removeClass("d-none");
        }
    });
};

// listens for user to click back button on page
let pageBackListener = function () {
    $(window).on("popstate", function () {
        // for now, just reloads
        location.reload();
    });
};

// quick-skip to dashboard
let dashboardSkip = function () {
    $("#dashboard-skip").on("click", function (e) {
        e.preventDefault();
        scrollBottom("#main");
    });
};

// quick-skip to course search
let searchSkip = function () {
    $("#search-skip").on("click", function (e) {
        e.preventDefault();
        resetScroll("#main");
    });
};

// initialize all tooltips
let initTooltipsToasts = function () {
    let tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    let tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    $("#status-indicator").on("click", function (e) {
        e.preventDefault();
    });
};

// closes the navbar (mobile) on tap out
let navbarAutoclose = function () {
    $(document).click(function (event) {
        var click = $(event.target);
        var _open = $(".navbar-collapse").hasClass("show");
        if (_open && !click.hasClass("navbar-toggler")) {
            $(".navbar-toggler").click();
        }
    });
};

// listens for "Confirm" removal from waitlist
let blacklistListener = function () {
    $("button.btn-blacklist").on("click", function (e) {
        e.preventDefault();
        netid = e.target.getAttribute("data-netid");
        switchid = `#button-${netid}`;
        $(switchid).attr("disabled", true);
        $.post(`/add_to_blacklist/${netid}`, function (res) {
            // checks that user successfully removed from waitlist on back-end
            if (!res["isSuccess"]) {
                $(switchid).html("Failed");
                return;
            }
            $(`#admin-results-${netid}`).remove();
            $(
                "#blacklisted"
            ).append(`<tr id='button-removal-${netid}' class='dashboard-course-row'><td>
                    ${netid}
                </td>
                <td>
                    <button type='button' id='button-remove-${netid}' data-netid=${netid} class='btn btn-sm btn-warning btn-blacklist-removal'>remove</button>
                </td>    
            </tr>`);
            $(document).on("click", `#button-remove-${netid}`, function (e) {
                e.preventDefault();
                netid = e.target.getAttribute("data-netid");
                $(`#button-remove-${netid}`).attr("disabled", true);
                $.post(`/remove_from_blacklist/${netid}`, function (res) {
                    // checks that user successfully removed from waitlist on back-end
                    if (!res["isSuccess"]) {
                        $(`#button-remove-${netid}`).attr("disabled", false);
                        return;
                    }
                    $(`#button-removal-${netid}`).remove();
                });
            });
        });
    });
};

// listens for "Confirm" removal from waitlist
let blacklistRemovalListener = function () {
    $("button.btn-blacklist-removal").on("click", function (e) {
        e.preventDefault();
        netid = e.target.getAttribute("data-netid");
        switchid = `#button-remove-${netid}`;
        $(switchid).attr("disabled", true);
        $.post(`/remove_from_blacklist/${netid}`, function (res) {
            // checks that user successfully removed from waitlist on back-end
            if (!res["isSuccess"]) {
                $(switchid).attr("disabled", false);
                return;
            }
            $(`#button-removal-${netid}`).remove();
        });
    });
};

// enables all admin function buttons
let enableAdminFunction = function () {
    $(".btn-blacklist").attr("disabled", false);
    $("#clear-all").attr("disabled", false);
    $("#toggle-emails").attr("disabled", false);
    $("#classid-clear-input").attr("disabled", false);
    $("#classid-clear-submit").attr("disabled", false);
    $("#courseid-clear-input").attr("disabled", false);
    $("#courseid-clear-submit").attr("disabled", false);
    $("#get-user-data-input").attr("disabled", false);
    $("#get-user-data-submit").attr("disabled", false);
};

// disables all admin function buttons
let disableAdminFunction = function () {
    $(".btn-blacklist").attr("disabled", true);
    $("#clear-all").attr("disabled", true);
    $("#toggle-emails").attr("disabled", true);
    $("#classid-clear-input").attr("disabled", true);
    $("#classid-clear-submit").attr("disabled", true);
    $("#courseid-clear-input").attr("disabled", true);
    $("#courseid-clear-submit").attr("disabled", true);
    $("#get-user-data-input").attr("disabled", true);
    $("#get-user-data-submit").attr("disabled", true);
};

// listens for email notifications switch toggle
let toggleEmailNotificationsListener = function () {
    $("#toggle-emails").on("click", function (e) {
        e.preventDefault();
        disableAdminFunction();

        if (!confirm("Are you sure you want to toggle notifications?")) {
            enableAdminFunction();
            return;
        }

        $.post("/get_notifications_status", function (res) {
            $.post(`/set_notifications_status/${!res["isOn"]}`, function (res1) {
                if (!res["isOn"]) {
                    $(".toast-container").prepend(
                        toastEmailsOn.clone().attr("id", "toast-emails-on-" + ++i)
                    );
                    $("#toast-emails-on-" + i).toast("show");
                } else {
                    $(".toast-container").prepend(
                        toastEmailsOff.clone().attr("id", "toast-emails-off-" + ++i)
                    );
                    $("#toast-emails-off-" + i).toast("show");
                }
                setTimeout(() => location.reload(), 3100);
            });
        });
    });
};

// sets the state of the toggle notifications button
let initToggleEmailNotificationsButton = function () {
    $.post("/get_notifications_status", function (res) {
        if (res["isOn"]) $("#toggle-emails").html("Turn Off");
        else $("#toggle-emails").html("Turn On");
        enableAdminFunction();
    });
};

// listens for "Confirm" removal from waitlist
let clearAllWaitlistListener = function () {
    $("#clear-all").on("click", function (e) {
        e.preventDefault();
        disableAdminFunction();

        if (
            !confirm("Are you sure you want to clear all waitlists? This action is irreversible.")
        ) {
            enableAdminFunction();
            return;
        }

        $.post("/clear_all_waitlists", function (res) {
            // checks that user successfully removed from waitlist on back-end
            if (!res["isSuccess"]) {
                enableAdminFunction();
                return;
            }
            enableAdminFunction();
        });
    });
};

// listens for "Confirm" removal from waitlist
let clearClassWaitlistListener = function () {
    $("#classid-clear").on("submit", function (e) {
        e.preventDefault();
        classid = $("#classid-clear-input").val();
        disableAdminFunction();
        $.post(`/clear_by_class/${classid}`, function (res) {
            // checks that user successfully removed from waitlist on back-end
            if (!res["isSuccess"]) {
                enableAdminFunction();
            }
            enableAdminFunction();
        });
    });
};

// listens for "Confirm" removal from waitlist
let clearCourseWaitlistListener = function () {
    $("#courseid-clear").on("submit", function (e) {
        e.preventDefault();
        courseid = $("#courseid-clear-input").val();
        disableAdminFunction();
        $.post(`/clear_by_course/${courseid}`, function (res) {
            // checks that user successfully removed from waitlist on back-end
            if (!res["isSuccess"]) {
                enableAdminFunction();
                return;
            }
            enableAdminFunction();
        });
    });
};

// listens for get_user_data query
let getUserDataListener = function () {
    $("#get-user-data").on("submit", function (e) {
        e.preventDefault();
        netid = $("#get-user-data-input").val();
        disableAdminFunction();
        $.post(`/get_user_data/${netid}`, function (res) {
            if (!res["data"]) {
                $(".toast-container").prepend(
                    toastUserDoesNotExist.clone().attr("id", "toast-user-does-not-exist-" + ++i)
                );
                $("#toast-user-does-not-exist-" + i).toast("show");
                enableAdminFunction();
                return;
            }
            let data = res["data"].split(",");
            $("#get-user-data-input").val("");

            dataHTML = "";
            for (let d of data) dataHTML += `<p>${d}</p>`;

            $("#modal-body-user-data").html(dataHTML);
            $("#user-data-waitlist-modal").modal("show");
            $("#staticBackdropLabelUserData").html(`Subscribed Sections for ${netid}`);

            enableAdminFunction();
        });
    });
};

// jQuery 'on' only applies listeners to elements currently on DOM
// applies listeners to current elements when document is loaded
$(document).ready(function () {
    searchFormListener();
    searchResultListener();
    switchListener();
    showAllListener();
    modalCancelListener();
    modalConfirmListener();
    dashboardCourseSelectListener();
    // modalCloseListener();
    pageBackListener();
    dashboardSkip();
    searchSkip();
    initTooltipsToasts();
    navbarAutoclose();
    blacklistListener();
    blacklistRemovalListener();
    clearAllWaitlistListener();
    clearClassWaitlistListener();
    clearCourseWaitlistListener();
    getUserDataListener();
    initToggleEmailNotificationsButton();
    toggleEmailNotificationsListener();
});
