// listens for submission of search form
let scrollTo = function (dest) {
    $(dest).animate(
        {
            scrollTop: $(dest)[0].scrollHeight - $(dest)[0].clientHeight,
        },
        500
    );
};

let resetScroll = function (dest) {
    $(dest).animate(
        {
            scrollTop: 0,
        },
        500
    );
};

let searchFormListener = function () {
    $("form#search-form").on("submit", function (e) {
        e.preventDefault();

        // get serach query
        query = $("#search-form-input").prop("value");
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

        // blur frame while loadidng
        $("#right-wrapper").css("pointer-events", "none");
        $("#right-wrapper").css("pointer", "wait");
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

        scrollTo("#main");

        // get course information
        $.post(`/courseinfo/${courseid}`, function (res) {
            // change search form to /course endpoint
            $("form#search-form").attr("action", "/course");
            $("input#search-form-courseid").attr("value", courseid);
            $("#right-wrapper").html(res);

            // unblur frame
            $("#right-wrapper").css("filter", "");
            $("#right-wrapper").css("pointer", "");
            $("#right-wrapper").css("pointer-events", "");
            // focusSearch();

            // update URL
            window.history.pushState({ restore: "right", html: res }, "", course_link);

            // add listener to new switches & modals
            switchListener();
            filterFullListener();
            modalCancelListener();
            modalConfirmListener();
        });
    });
};

// listens for toggle of waitlist notification switch
let switchListener = function () {
    $("input.waitlist-switch").change(function (e) {
        e.preventDefault();
        classid = e.target.getAttribute("data-classid");

        $("#confirm-remove-waitlist").attr("data-classid", classid);

        switchid = `#switch-${classid}`;

        // if user is not on waitlist for this class, then add them
        if (!$(switchid).attr("checked")) {
            $.post(`/add_to_waitlist/${classid}`, function (res) {
                // checks that user successfully added to waitlist on back-end
                if (!res["isSuccess"]) {
                    console.log(`Failed to add to waitlist for class ${classid}`);
                    return;
                }
                $(switchid).attr("checked", true);
                $(switchid).attr("data-bs-toggle", "modal");
                $(switchid).attr("data-bs-target", "#confirm-remove-waitlist");
                console.log(`Successfully added to waitlist for class ${classid}`);
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
        $.post(`/remove_from_waitlist/${classid}`, function (res) {
            // checks that user successfully removed from waitlist on back-end
            if (!res["isSuccess"]) {
                console.log(`Failed to remove from waitlist for class ${classid}`);
                return;
            }
            $(`${switchid}.dashboard-switch`).closest("tr.dashboard-course-row").remove();
            $(switchid).removeAttr("checked");
            $(switchid).removeAttr("data-bs-toggle");
            $(switchid).removeAttr("data-bs-target");

            console.log(`Successfully removed from waitlist for class ${classid}`);
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

let focusSearch = function () {
    $("#search-form-input").focus();
};

let filterFullListener = function () {
    $("#filter-full-check").on("click", function (e) {
        if ($(this).prop("checked")) {
            $(".available-section-row").addClass("d-none");
        } else {
            $(".available-section-row").removeClass("d-none");
        }
    });
};

// listens for user to click back button on page
let pageBackListener = function () {
    $(window).on("popstate", function () {
        // for now, just reloads
        location.reload();

        // html = window.history.state['html'];
        // restore = window.history.state['restore'];
        // if (restore === 'right') {
        //     $("#right-wrapper").html(html);
        // }
        // else if (restore === 'search') {
        //     $("div#search-results").html(html);
        // }
        // else {
        // }
    });
};

let dashboardSkip = function () {
    $("#dashboard-skip").on("click", function (e) {
        e.preventDefault();
        scrollTo("#main");
    });
};

// jQuery 'on' only applies listeners to elements currently on DOM
// applies listeners to current elements when document is loaded
$(document).ready(function () {
    focusSearch();
    searchFormListener();
    searchResultListener();
    switchListener();
    filterFullListener();
    modalCancelListener();
    modalConfirmListener();
    pageBackListener();
    dashboardSkip();
});
