// $('form#search-form').submit(function(e) {
    //   e.preventDefault();

    //   query = $('#search-form-input').prop('value')
    //   params = location.search
    //   curr_path = location.pathname
    //   if (params === '') {
    //     curr_path = curr_path + '?query=' + query
    //   }
    //   else {
    //     curr_path = curr_path + '?'
    //     params = params.replace('?', '')
    //     arr = params.split("&")
    //     for (let i=0; i < arr.length; i++) {
    //       if (i > 0) curr_path += '&'
    //       if (arr[i].startsWith('query'))
    //           curr_path = curr_path + 'query=' + query
    //       else
    //           curr_path += arr[i]
    //     }
    //   }
    //   $.get(`${curr_path}&update=search`,
    //         function(res) {
    //           console.log(res)
    //           $('div#search-results').html(res)
    //           window.history.pushState(res, '', curr_path)
    //       });

    // })

    // $(window).on("popstate", function () {
    //     prevState = window.history.state
    //     if(prevState) {
    //       $('div#search-results').html(prevState)
    //     }
    //     else {
    //       location.reload();
    //     }
    // });