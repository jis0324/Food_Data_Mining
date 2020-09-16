$(document).ready(function () {
    // setting table as Datatable
    let table = $('#products_table').DataTable({
        "dom": '<"top">rt<"bottom"lp><"clear">'
    });

    // Global filter type select event
    $('.global-search-wrapper .dropdown-menu .dropdown-item').on('click', function () {
        event.preventDefault(); //prevent default action

        let selected_filter_type = $(this).html();
        $('.global-search-wrapper button.global-search-sel-btn').html(selected_filter_type);
        $('.global-search-wrapper button.global-search-sel-btn').attr('filter_type', $(this).data('value'));
        $('.global-search-wrapper .global-filter-input').val('');
    });

    // Global filter
    $('.global-search-wrapper .global-filter-input').on('keyup', function() {
        // Event listener to the two range filtering inputs to redraw on input
        table.draw();
    });

    // Category Filter
    $('.criteria-search-wrapper .category_filter_input').on('keyup', function() {
        let category_filter_key = $('.criteria-search-wrapper .category_filter_input').val();
        table.columns(3).search(category_filter_key).draw();
    });

    // Brand Filter
    $('.criteria-search-wrapper .brand_filter_input').on('keyup', function() {
        let category_filter_key = $('.criteria-search-wrapper .brand_filter_input').val();
        table.columns(2).search(category_filter_key).draw();
    });

    // Website Filter
    $('.criteria-search-wrapper .website_filter_input').on('keyup', function() {
        let category_filter_key = $('.criteria-search-wrapper .website_filter_input').val();
        table.columns(1).search(category_filter_key).draw();
    });

    $('.bookmark-onoffswitch .onoffswitch-checkbox').on('click', function() {
        if ($(this).is(':checked')) {
            $(this).attr('checked', true);
        } else {
            $(this).removeAttr('checked');
        }

        table.draw();
    });

    $('.exclude-onoffswitch .onoffswitch-checkbox').on('click', function() {
        if ($(this).is(':checked')) {
            $(this).attr('checked', true);

            $.ajax({
                url: '/get_excluded_products',
                type: 'POST',
                contentType: 'application/json;charset=UTF-8',
            }).done(function (response) { //
                response = JSON.parse(response);
                console.log(response);
                table.clear();
                if ($.fn.DataTable.isDataTable('#products_table')) {
                    table.destroy();
                }
                $.each(response, function (i, data) {
                    let tr_body = draw_tbody(data);
                    $('#products_table').append(tr_body);
                });
                table = $('#products_table').DataTable();
            });
        } else {
            $(this).removeAttr('checked');
            $.ajax({
                url: '/get_unexcluded_products',
                type: 'POST',
                contentType: 'application/json;charset=UTF-8',
            }).done(function (response) { //
                response = JSON.parse(response);
                console.log(response);
                table.clear();
                if ($.fn.DataTable.isDataTable('#products_table')) {
                    table.destroy();
                }
                $.each(response, function (i, data) {
                    let tr_body = draw_tbody(data);
                    $('#products_table').append(tr_body);
                });
                table = $('#products_table').DataTable();
            });
        }
    });

    // click bookmark
    $("#products_table").on("click", ".tr-row td .bookmark-icon", function () {
        let bookmark_icon = $(this);
        let product_uid = bookmark_icon.parent().parent().attr('id');

        if (bookmark_icon.hasClass("fa-bookmark-o")) {
            $.ajax({
                url: '/add_bookmark',
                type: 'POST',
                data: JSON.stringify({'uid' : product_uid}),
                contentType: 'application/json;charset=UTF-8',
            }).done(function (response) {
                if (response == 'False') {
                    alert("Raised Some Error!, Please try again.")
                } else {
                    response = JSON.parse(response);

                    let first_td = "<td>"+response[4]+"</td>";
                    let second_td = "<td>"+response[3]+"</td>";
                    let third_td = "<td>"+response[7]+"</td>";
                    let fourth_td = "<td>"+response[6]+"</td>";

                    let fifth_td = "";
                    if (response[16]) {
                        fifth_td = "<td>"+response[16]+"</td>"
                    } else {
                        fifth_td = "<td></td>"
                    }

                    let sixth_td = "";
                    if (response[17]) {
                        sixth_td = "<td>"+response[17]+"</td>"
                    } else {
                        sixth_td = "<td></td>"
                    }

                    let seventh_td = "";
                    if (response[18]) {
                        seventh_td = "<td>"+response[18]+"</td>"
                    } else {
                        seventh_td = "<td></td>"
                    }

                    let eighth_td = ''
                    if (response[14]) {
                        eighth_td = "<td><i class='bookmark-icon fa fa-bookmark pink-color cursor-pointer' aria-hidden='true'><span class='d-none'>bookmarked</span></i></td>";
                    } else {
                        eighth_td = "<td><i class='bookmark-icon fa fa-bookmark-o cursor-pointer' aria-hidden='true'><span class='d-none'></span></i></td>";
                    }

                    let ninth_td = ''
                    if (response[15]) {
                        ninth_td = "<td><i class='exclude-icon fa fa-times text-danger cursor-pointer' aria-hidden='true'><span class=d-none>exclude</span></i></td>";
                    } else {
                        ninth_td = "<td><i class='exclude-icon fa fa-times cursor-pointer' aria-hidden='true'><span class='d-none'></span></i></td>";
                    }

                    let tr_row = [first_td, second_td, third_td, fourth_td, fifth_td, sixth_td, seventh_td, eighth_td, ninth_td]
                    table.row("#" + product_uid).data(tr_row).invalidate().draw(false)
                }
            });
        } else {
            $.ajax({
                url: '/remove_bookmark',
                type: 'POST',
                data: JSON.stringify({'uid' : product_uid}),
                contentType: 'application/json;charset=UTF-8',
            }).done(function (response) {
                if (response == 'False') {
                    alert("Raised Some Error!, Please try again.")
                } else {
                    response = JSON.parse(response);

                    let first_td = "<td>"+response[4]+"</td>";
                    let second_td = "<td>"+response[3]+"</td>";
                    let third_td = "<td>"+response[7]+"</td>";
                    let fourth_td = "<td>"+response[6]+"</td>";

                    let fifth_td = "";
                    if (response[16]) {
                        fifth_td = "<td>"+response[16]+"</td>"
                    } else {
                        fifth_td = "<td></td>"
                    }

                    let sixth_td = "";
                    if (response[17]) {
                        sixth_td = "<td>"+response[17]+"</td>"
                    } else {
                        sixth_td = "<td></td>"
                    }

                    let seventh_td = "";
                    if (response[18]) {
                        seventh_td = "<td>"+response[18]+"</td>"
                    } else {
                        seventh_td = "<td></td>"
                    }

                    let eighth_td = ''
                    if (response[14]) {
                        eighth_td = "<td><i class='bookmark-icon fa fa-bookmark pink-color cursor-pointer' aria-hidden='true'><span class='d-none'></span></i></td>";
                    } else {
                        eighth_td = "<td><i class='bookmark-icon fa fa-bookmark-o cursor-pointer' aria-hidden='true'><span class='d-none'></span></i></td>";
                    }

                    let ninth_td = ''
                    if (response[15]) {
                        ninth_td = "<td><i class='exclude-icon fa fa-times text-danger cursor-pointer' aria-hidden='true'><span class=d-none>exclude</span></i></td>";
                    } else {
                        ninth_td = "<td><i class='exclude-icon fa fa-times cursor-pointer' aria-hidden='true'><span class='d-none'></span></i></td>";
                    }

                    let tr_row = [first_td, second_td, third_td, fourth_td, fifth_td, sixth_td, seventh_td, eighth_td, ninth_td]
                    table.row("#" + product_uid).data(tr_row).invalidate().draw(false)
                }
            });
        }
    });

    // click exclude
    $("#products_table").on("click", ".tr-row td .exclude-icon", function () {
        let exclude_icon = $(this);
        let product_uid = exclude_icon.parent().parent().attr('id');

        if (exclude_icon.hasClass("text-danger")) {
            $.ajax({
                url: '/remove_exclude',
                type: 'POST',
                data: JSON.stringify({'uid' : product_uid}),
                contentType: 'application/json;charset=UTF-8',
            }).done(function (response) { //
                table.row("#" + product_uid).remove().draw(false);
            });
        } else {
            $.ajax({
                url: '/add_exclude',
                type: 'POST',
                data: JSON.stringify({'uid' : product_uid}),
                contentType: 'application/json;charset=UTF-8',
            }).done(function (response) { //
                table.row("#" + product_uid).remove().draw(false);
            });
        }
    });

});

$.fn.dataTable.ext.search.push(
    function( settings, data, dataIndex ) {
        let filter_key = $('.global-search-wrapper .global-filter-input').val();
        let filter_type = $(".global-search-sel-btn").html()

        let interface_bookmark_flag = false;

        if ($('.onoffswitch .onoffswitch-checkbox').attr('checked')) {
            interface_bookmark_flag = true;
        }

        if (filter_type == 'All') {
            for (let i=0; i < data.length; i++) {
                if (data[i].includes(filter_key)) {
                    if (interface_bookmark_flag) {
                        if (data[7].includes('bookmarked')) {
                            return true
                        }
                    } else {
                        return true
                    }
                }
            }
            return false
        } else {
            let table_head_list = ['Product', 'Product URL', 'Brand', 'Category', 'Last Price', 'Current Price', '% Discount', 'Bookmark', 'Exclude'];
            let thead_index = table_head_list.indexOf(filter_type);
            if (data[thead_index].includes(filter_key)) {
                if (data[thead_index].includes(filter_key)) {
                    if (interface_bookmark_flag) {
                        if (data[7] == 'bookmarked') {
                            return true
                        }
                    } else {
                        return true
                    }
                }
            }
            return false;
        }

    }
);

function draw_tbody(data) {
    let first_td = "<td>"+data[4]+"</td>";
    let second_td = "<td>"+data[3]+"</td>";
    let third_td = "<td>"+data[7]+"</td>";
    let fourth_td = "<td>"+data[6]+"</td>";

    let fifth_td = "";
    if (data[16]) {
        fifth_td = "<td>"+data[16]+"</td>"
    } else {
        fifth_td = "<td></td>"
    }

    let sixth_td = "";
    if (data[17]) {
        sixth_td = "<td>"+data[17]+"</td>"
    } else {
        sixth_td = "<td></td>"
    }

    let seventh_td = "";
    if (data[18]) {
        seventh_td = "<td>"+data[18]+"</td>"
    } else {
        seventh_td = "<td></td>"
    }

    let eighth_td = ''
    if (data[14]) {
        eighth_td = "<td><i class='bookmark-icon fa fa-bookmark pink-color cursor-pointer' aria-hidden='true'><span class='d-none'>bookmarked</span></i></td>";
    } else {
        eighth_td = "<td><i class='bookmark-icon fa fa-bookmark-o cursor-pointer' aria-hidden='true'><span class='d-none'></span></i></td>";
    }

    let ninth_td = ''
    if (data[15]) {
        ninth_td = "<td><i class='exclude-icon fa fa-times text-danger cursor-pointer' aria-hidden='true'><span class=d-none>exclude</span></i></td>";
    } else {
        ninth_td = "<td><i class='exclude-icon fa fa-times cursor-pointer' aria-hidden='true'><span class='d-none'></span></i></td>";
    }

    let tr_body = '<tr class="tr-row" id="'+data[0]+'">'+first_td+second_td+third_td+fourth_td+fifth_td+sixth_td+seventh_td+eighth_td+ninth_td+'</tr>';
    return tr_body;
}