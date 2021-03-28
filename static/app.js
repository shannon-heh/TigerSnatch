$(document).ready(function() {
  // dynamically loads course details when search result is clicked
    $('a.search-results-link').click(function(e) {
      e.preventDefault();

      $('#right-wrapper').css("pointer-events", "none")
      $('#right-wrapper').css("pointer", "wait")
      $('#right-wrapper').css("filter", "blur(2px)")

      closest_a = $(this).closest('a')
      course_link = closest_a.attr('href')
      courseid = closest_a.attr('data-courseid')

      $.get(`${course_link}&updateSearch=false`,
            function(res) {
              console.log(res)
              $('form#search-form').attr('action', '/course')
              $('input#search-form-courseid').attr('value', courseid)
              $('#right-wrapper').html(res)
              window.history.pushState(res, '', course_link)
              
              $('#right-wrapper').css("filter", "")
              $('#right-wrapper').css("pointer", "")
              $('#right-wrapper').css("pointer-events", "")
          });
    })

    // handles going back to previous page
    $(window).on("popstate", function () {
        prevState = window.history.state
        if(prevState) {
          $('#right-wrapper').html(prevState)
        }
        else {
          location.reload();
        }
    });
});

  // Handles user toggle switch off to remove from waitlist 
  // and modal dialog pops up
  $(document).ready(function() {
    // listener for modal "Cancel" button 
    $('#waitlist-modal-cancel').click(function(e) {
      e.preventDefault()
      classid = $('#confirm-remove-waitlist').attr('data-classid');
      $('#switch-'+classid).prop('checked', true)
    })

    // listener for modal "Confirm" button 
    $('#waitlist-modal-confirm').click(function(e) {
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
  });

  // links client-side and backend logic for add and remove from waitlist 
  $(document).ready(function() {
    // listener for waitlist "switch"
    $('input.waitlist-switch').change(function(e) {
      e.preventDefault()
      classid = e.target.getAttribute("data-classid")

      $('#confirm-remove-waitlist').attr('data-classid',classid);
      
      // if user is not on waitlist for this class
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
       return false;
    });
  });

  