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
            restripeTables();

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
            $(switchid).attr("disabled", true)
            $.post(`/add_to_waitlist/${classid}`, function (res) {
                // checks that user successfully added to waitlist on back-end
                if (res["isSuccess"] === 2) {
                    // console.log(`Failed to add to waitlist for class ${classid}`);
                    $(switchid).attr("disabled", false)
                    return;
                }
                if (res['isSuccess'] === 0) {
                    console.log('youre full lol')
                    $('#close-waitlist-modal').modal('show');
                    $(switchid).attr("checked", false);
                    $(switchid).prop("checked", false);
                    $(switchid).attr("disabled", false)
                    return
                }
                $(switchid).attr("checked", true);
                $(switchid).attr("data-bs-toggle", "modal");
                $(switchid).attr("data-bs-target", "#confirm-remove-waitlist");
                $(switchid).attr("disabled", false)

                $(".toast-container").prepend(toastAdded.clone().attr("id", "toast-added-" + ++i));
                $("#toast-added-" + i).toast("show");
                // console.log(`Successfully added to waitlist for class ${classid}`);
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
        $(switchid).attr("disabled", true)
        $.post(`/remove_from_waitlist/${classid}`, function (res) {
            // checks that user successfully removed from waitlist on back-end
            if (!res["isSuccess"]) {
                // console.log(`Failed to remove from waitlist for class ${classid}`);
                $(switchid).attr("disabled", false)
                return;
            }
            $(`${switchid}.dashboard-switch`).closest("tr.dashboard-course-row").remove();
            $(switchid).removeAttr("checked");
            $(switchid).removeAttr("data-bs-toggle");
            $(switchid).removeAttr("data-bs-target");
            $(switchid).attr("disabled", false)

            $(".toast-container").prepend(toastRemoved.clone().attr("id", "toast-removed-" + ++i));
            $("#toast-removed-" + i).toast("show");
            // console.log(`Successfully removed from waitlist for class ${classid}`);
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

<<<<<<< HEAD
// listens for "Close" from waitlist warning
// let modalCloseListener = function () {
//     $("#waitlist-modal-close").on("click", function (e) {
//         e.preventDefault();
//         classid = $("#close-waitlist-modal").attr("data-classid");
//         $(`#switch-${classid}`).prop("checked", false);
//     });
// };

let filterFullListener = function () {
    $("#filter-full-check").on("click", function (e) {
=======
let showAllListener = function () {
    $("#show-all-check").on("click", function (e) {
>>>>>>> 74e73f1928005b48cb62d7a839ce065b887b5527
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
};

let restripeTables = function() {
    // $("tr:visible").each( function(index, obj) {
    //     if (index % 2) {
    //         $(this).addClass('visible-odd').removeClass('visible-even');
    //     } else {
    //         $(this).addClass('visible-even').removeClass('visible-odd');
    //     }
    // });

    // $("table").removeAttr('--bs-table-striped-bg')
}

// jQuery 'on' only applies listeners to elements currently on DOM
// applies listeners to current elements when document is loaded
$(document).ready(function () {
    searchFormListener();
    searchResultListener();
    switchListener();
    showAllListener();
    modalCancelListener();
    modalConfirmListener();
    // modalCloseListener();
    pageBackListener();
    dashboardSkip();
    searchSkip();
    initTooltipsToasts();
    restripeTables();
});
