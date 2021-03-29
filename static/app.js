// listens for submission of search form
let searchFormListener = function() {
    $('form#search-form').on('submit', function(e) {
      e.preventDefault();
      
      // get serach query
      query = $('#search-form-input').prop('value')

      // construct new URL
      params = location.search
      curr_path = location.pathname
      if (params === '') {
        curr_path = curr_path + '?query=' + query
      }
      else {
        curr_path = curr_path + '?'
        params = params.replace('?', '')
        arr = params.split("&")
        for (let i=0; i < arr.length; i++) {
          if (i > 0) curr_path += '&'
          if (arr[i].startsWith('query'))
              curr_path = curr_path + 'query=' + query
          else
              curr_path += arr[i]
        }
      }

      // get search results 
      if (query.trim() === '') {
          endpoint = '/searchresults'
      }
      else {
          endpoint = `/searchresults/${query}`
      }
      $.post(endpoint,
            function(res) {
              $('div#search-results').html(res)
              window.history.pushState(res, '', curr_path)
              // adds listener to new search results
              searchResultListener(); 
          });
    })
}

// listens for selection of search result
let searchResultListener = function() {
  $('.search-results-link').on('click', function(e) {
    e.preventDefault();

    // blur frame while loadidng 
    $('#right-wrapper').css("pointer-events", "none")
    $('#right-wrapper').css("pointer", "wait")
    $('#right-wrapper').css("filter", "blur(2px)")

    closest_a = $(this).closest('a')
    course_link = closest_a.attr('href')
    courseid = closest_a.attr('data-courseid')

    // get course information 
    $.post(`/courseinfo/${courseid}`,
          function(res) {
            // change search form to /course endpoint
            $('form#search-form').attr('action', '/course')
            $('input#search-form-courseid').attr('value', courseid)
            $('#right-wrapper').html(res)

            // unblur frame
            $('#right-wrapper').css("filter", "")
            $('#right-wrapper').css("pointer", "")
            $('#right-wrapper').css("pointer-events", "")

            // update URL
            window.history.pushState(res, '', course_link)

            // add listener to new switches & modals 
            switchListener();
            modalCancelListener();
            modalConfirmListener();
        });
  }) 
}
  
// listens for toggle of waitlist notification switch
let switchListener = function() {
  $('input.waitlist-switch').change(function(e) {
    e.preventDefault()
    classid = e.target.getAttribute("data-classid")

    $('#confirm-remove-waitlist').attr('data-classid',classid);
    
    // if user is not on waitlist for this class, then add them
    if(!$('#switch-'+classid).attr('checked')) {
        $.post(`/add_to_waitlist/${classid}`,
          function(res) {
            // checks that user successfully added to waitlist on back-end
            if (!res["isSuccess"]) {
              console.log(`Failed to add to waitlist for class ${classid}`)
              return
            }
            $('#switch-'+classid).attr('checked', true)
            $('#switch-'+classid).attr('data-bs-toggle', 'modal')
            $('#switch-'+classid).attr('data-bs-target', '#confirm-remove-waitlist')
            console.log(`Successfully added to waitlist for class ${classid}`)
        });
    }
  });
}

// listens for "Confirm" removal from waitlist
let modalConfirmListener = function() {
  $('#waitlist-modal-confirm').on('click', function(e) {
    e.preventDefault()
    classid = $('#confirm-remove-waitlist').attr('data-classid');
    $.post(`/remove_from_waitlist/${classid}`,
          function(res) {
            // checks that user successfully removed from waitlist on back-end
            if (!res["isSuccess"]) {
              console.log(`Failed to remove from waitlist for class ${classid}`)
              return
            }
            $('#switch-'+classid).removeAttr('checked')
            $('#switch-'+classid).removeAttr("data-bs-toggle")
            $('#switch-'+classid).removeAttr("data-bs-target")

            console.log(`Successfully removed from waitlist for class ${classid}`)
        });
  })
}

// listens for "Cancel" removal from waitlist 
let modalCancelListener = function() {
  $('#waitlist-modal-cancel').on('click', function(e) {
    e.preventDefault()
    classid = $('#confirm-remove-waitlist').attr('data-classid');
    $('#switch-'+classid).prop('checked', true)
  })
}

// listens for user to click back button on page
let pageBackListener = function() {
   $(window).on("popstate", function () {
      prevState = window.history.state
      if(prevState) {
        $('#right-wrapper').html(prevState)
      }
      else {
        location.reload();
      }
  });
}

// jQuery 'on' only applies listeners to elements currently on DOM
// applies listeners to current elements when document is loaded
$(document).ready(function() {
  searchFormListener();
  searchResultListener();
  switchListener();
  modalCancelListener();
  modalConfirmListener();
  pageBackListener();
});
