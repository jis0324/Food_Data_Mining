$(document).ready(function () {
    // setting table as Datatable
    let table = $('#products_table').DataTable({
        "dom": '<"top">rt<"bottom"lp><"clear">'
        // "dom": '<"top">rt<"bottom"<"#table_info_wrapper.d-flex" and il>p><"clear">'
    });

    // Global filter type select event
    $('.global-search-wrapper .dropdown-menu .dropdown-item').on('click', function () {
        event.preventDefault(); //prevent default action

        let selected_filter_type = $(this).html();
        $('.global-search-wrapper button.global-search-sel-btn').html(selected_filter_type);
        $('.global-search-wrapper button.global-search-sel-btn').attr('filter_type', $(this).data('value'));
    });

    // Golbal filter
    $('.global-search-wrapper .global-filter-input').on('change',function() {
        let value = $(this).val();
        var filteredData = table
            .columns( [0, 1] )
            .flatten()
            .filter( function ( value, index ) {
                return  $(this).text().indexOf("whatever") !== -1;
            });
    });


	$('#crawl_result_table tbody').on('click', '.claim', function () {
		document.getElementById("claim_people_form").reset();
		$('#claimModal #claim_sumbit_btn').attr('disabled', 'true');

		$('#l_name_modal').val($('#l_name_search').val());
		$('#heldin_modal').val($(this).parent().parent().children('.heldin-td').text())
		$('#last_address_modal').val($(this).parent().parent().children('.last-address-td').text())
		$('#property_id_modal').val($(this).parent().parent().children('.property-id-td').text())
		$('#reported_by_modal').val($(this).parent().parent().children('.reported-by-td').text())
		$('#amount_modal').val($(this).parent().parent().children('.amount-td').text())
		$('#claimModal').modal();
	});

	$('#claimModal #customCheck').change(function () {
		if ($('#claimModal #claim_sumbit_btn').attr('disabled')) {
			$('#claimModal #claim_sumbit_btn').removeAttr('disabled');
		} else {
			$('#claimModal #claim_sumbit_btn').attr('disabled', 'true');
		}
	});

	$("#search_form").submit(function (event) {
		event.preventDefault(); //prevent default action 

		$('.loading-section').removeClass('hide');
		$('.crawl-section').addClass('loading');

		let post_url = $(this).attr("action"); //get form action url
		let request_method = $(this).attr("method"); //get form GET/POST method
		let form_data = $(this).serialize(); //Encode form elements for submission
		let thread_status = '';

		pullData = setInterval(
			function () {
				$.ajax({
					url: post_url,
					type: request_method,
					data: form_data + "&thread_status=" + thread_status,
				}).done(function (result) { //
					response = JSON.parse(result);
					response_data = response[0];
					thread_status = response[1];
					let tbody = '';
					
					if (thread_status == 'end') {
						clearInterval(pullData);
						$('.loading-section').addClass('hide');
						$('.crawl-section').removeClass('loading');
						$('.crawl-section .table-div').removeClass('hide');
					} else if (thread_status == 'crawling') {
						if (response_data.length > 0) {
							for (let i = 0; i < response_data.length; i++) {
								tbody += '<tr>'
								tbody += '<td> <button class="btn btn-info claim-btn claim" data-lname="' + form_data['l_name_search'] + '">Claim</button> </td>';
								tbody += '<td class="name-td">' + response_data[i][0] + '</td>';
								tbody += '<td class="heldin-td">' + response_data[i][1] + '</td>';
								tbody += '<td class="last-address-td">' + response_data[i][2] + '</td>';
								tbody += '<td class="property-id-td">' + response_data[i][3] + '</td>';
								tbody += '<td class="reported-by-td">' + response_data[i][4] + '</td>';
								tbody += '<td class="amount-td">' + response_data[i][5] + '</td>';
								tbody += '</tr>';
							}
							console.log(tbody)
							$('.loading-section').addClass('hide');
							$('.crawl-section').removeClass('loading');
							$('.crawl-section .table-div').removeClass('hide');
						}
					}

					$('.crawl-section .table-div #crawl_result_table tbody').html(tbody);
					if ($.fn.dataTable.isDataTable('#crawl_result_table')) {
						$('#crawl_result_table').DataTable();
					} else {
						$('#crawl_result_table').DataTable({
							"columns": [
								{ "orderable": false },
								null,
								null,
								null,
								null,
								null,
								null
							]
						});
					}
				})
			}
			, 5000);
	});

	$("#claim_people_form").submit(function (event) {
		event.preventDefault(); //prevent default action 
		$('#claimModal #claim_sumbit_btn').attr('disabled', 'true');

		$('.loading-section').removeClass('hide');
		$('.crawl-section').addClass('loading');

		let post_url = $(this).attr("action"); //get form action url
		let request_method = $(this).attr("method"); //get form GET/POST method
		let form_data = $(this).serialize(); //Encode form elements for submission

		$.ajax({
			url: post_url,
			type: request_method,
			data: form_data
		}).done(function (response) { //
			$('#claimModal').modal('hide');
			swal("SUCCESS!", "The people data saved successfully!", "success");

			$('.loading-section').addClass('hide');
			$('.crawl-section').removeClass('loading');
		});



	});

});
// $(document).ready(function () {

// 	let pullData;
// 	$('#crawl_result_table').DataTable();

// 	$('#crawl_result_table tbody').on('click', '.claim', function () {
// 		document.getElementById("claim_people_form").reset();
// 		$('#claimModal #claim_sumbit_btn').attr('disabled', 'true');

// 		$('#l_name_modal').val($('#l_name_search').val());
// 		$('#heldin_modal').val($(this).parent().parent().children('.heldin-td').text())
// 		$('#last_address_modal').val($(this).parent().parent().children('.last-address-td').text())
// 		$('#property_id_modal').val($(this).parent().parent().children('.property-id-td').text())
// 		$('#reported_by_modal').val($(this).parent().parent().children('.reported-by-td').text())
// 		$('#amount_modal').val($(this).parent().parent().children('.amount-td').text())
// 		$('#claimModal').modal();
// 	});

// 	$('#claimModal #customCheck').change(function () {
// 		if ($('#claimModal #claim_sumbit_btn').attr('disabled')) {
// 			$('#claimModal #claim_sumbit_btn').removeAttr('disabled');
// 		} else {
// 			$('#claimModal #claim_sumbit_btn').attr('disabled', 'true');
// 		}
// 	});

// 	$("#search_form").submit(function (event) {
// 		event.preventDefault(); //prevent default action 

// 		$('.loading-section').removeClass('hide');
// 		$('.crawl-section').addClass('loading');

// 		let post_url = $(this).attr("action"); //get form action url
// 		let request_method = $(this).attr("method"); //get form GET/POST method
// 		let form_data = $(this).serialize(); //Encode form elements for submission
// 		let thread_status = '';
// 		let tbody_data = []
// 		$('.crawl-section .table-div #crawl_result_table tbody').html('');

// 		pullData = setInterval(
// 			function () {
// 				$.ajax({
// 					url: post_url,
// 					type: request_method,
// 					data: form_data + "&thread_status=" + thread_status,
// 				}).done(function (result) { //
// 					response = JSON.parse(result);
// 					response_data = response[0];
// 					thread_status = response[1];

// 					if ( response_data.length > 0 ) {
// 						for (let i = 0; i < response_data.length; i++ )  {
//               tr_data = response_data[i].prepend('<button class="btn btn-info claim-btn claim" data-lname="' + form_data['l_name_search'] + '">Claim</button>')
// 							tbody_data.push(tr_data);
// 						}
// 					}
// 					console.log(response_data);
// 					console.log(tbody_data);
// 					let tbody = '';
					
// 					if (thread_status == 'end') {
// 						clearInterval(pullData);
// 						$('.loading-section').addClass('hide');
// 						$('.crawl-section').removeClass('loading');
// 						$('.crawl-section .table-div').removeClass('hide');
// 					} else if (thread_status == 'crawling') {
// 						if (tbody_data.length > 0) {
							
// 							$('.loading-section').addClass('hide');
// 							$('.crawl-section').removeClass('loading');
// 							$('.crawl-section .table-div').removeClass('hide');

// 							$(document).ready(function() {
							    
// 							    if ($.fn.dataTable.isDataTable('#crawl_result_table')) {
// 							    	var table = $('#crawl_result_table').DataTable();
// 									  table.destroy();
//         							$('#crawl_result_table').empty();
//         							$('#crawl_result_table').DataTable( {
// 								        data: tbody_data,
// 								        columns: [
// 								            { title: "" },
// 								            { title: "Name" },
// 								            { title: "Position" },
// 								            { title: "Office" },
// 								            { title: "Extn." },
// 								            { title: "Start date" },
// 								            { title: "Salary" }
// 								        ]
// 								    } );
// 								} else {
// 									$('#crawl_result_table').DataTable( {
// 								        data: tbody_data,
// 								        columns: [
// 								            { title: "" },
// 								            { title: "Name" },
// 								            { title: "Position" },
// 								            { title: "Office" },
// 								            { title: "Extn." },
// 								            { title: "Start date" },
// 								            { title: "Salary" }
// 								        ]
// 								    } );
// 								}
// 							} );
// 						}
// 					}

					
// 				})
// 			}
// 			, 5000);
// 	});

// 	$("#claim_people_form").submit(function (event) {
// 		event.preventDefault(); //prevent default action 
// 		$('#claimModal #claim_sumbit_btn').attr('disabled', 'true');

// 		$('.loading-section').removeClass('hide');
// 		$('.crawl-section').addClass('loading');

// 		let post_url = $(this).attr("action"); //get form action url
// 		let request_method = $(this).attr("method"); //get form GET/POST method
// 		let form_data = $(this).serialize(); //Encode form elements for submission

// 		$.ajax({
// 			url: post_url,
// 			type: request_method,
// 			data: form_data
// 		}).done(function (response) { //
// 			$('#claimModal').modal('hide');
// 			swal("SUCCESS!", "The people data saved successfully!", "success");

// 			$('.loading-section').addClass('hide');
// 			$('.crawl-section').removeClass('loading');
// 		});



// 	});

// });