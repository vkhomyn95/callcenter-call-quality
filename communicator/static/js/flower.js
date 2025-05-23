/*jslint browser: true */
/*global $, WebSocket, jQuery */

var flower = (function () {
    "use strict";

    var alertContainer = document.getElementById('alert-container');

    function show_alert(message, type) {
        var wrapper = document.createElement('div');
        wrapper.innerHTML = `
            <div class="alert alert-${type} alert-dismissible" role="alert">
                <div>${message}</div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>`;
        alertContainer.appendChild(wrapper);
    }

    function url_prefix() {
        var prefix = $('#url_prefix').val();
        if (prefix) {
            prefix = prefix.replace(/\/+$/, '');
            if (prefix.startsWith('/')) {
                return prefix;
            } else {
                return '/' + prefix;
            }
        }
        return '';
    }

    //https://github.com/DataTables/DataTables/blob/1.10.11/media/js/jquery.dataTables.js#L14882
    function htmlEscapeEntities(d) {
        return typeof d === 'string' ?
            d.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;') :
            d;
    }

    function active_page(name) {
        var pathname = $(location).attr('pathname');
        if (name === '/') {
            return pathname === (url_prefix() + name);
        } else {
            return pathname.startsWith(url_prefix() + name);
        }
    }

    function showErrorNotification(message) {
        const notification = document.createElement('ul');
        notification.className = 'notifications';
        notification.innerHTML = `
            <li class="toast error">
                <div class="column">
                   <span>${message}</span>
                </div>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" onclick="removeToast(this.parentElement)">
                    <path d="M18 6L6 18" stroke="#333333" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M6 6L18 18" stroke="#333333" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </li>
        `

        document.body.appendChild(notification);

        setTimeout(() => {
            document.body.removeChild(notification);
        }, 3000);
    }

    $('#worker-refresh').on('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        $('.dropdown-toggle').dropdown('hide');

        var workername = $('#workername').text();

        $.ajax({
            type: 'GET',
            url: url_prefix() + '/api/workers',
            dataType: 'json',
            data: {
                workername: unescape(workername),
                refresh: 1
            },
            success: function (data) {
                show_alert(data.message || 'Successfully refreshed', 'success');
            },
            error: function (data) {
                show_alert(data.responseText, "danger");
            }
        });
    });

    $('#worker-refresh-all').on('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        $('.dropdown-toggle').dropdown('hide');

        $.ajax({
            type: 'GET',
            url: url_prefix() + '/api/workers',
            dataType: 'json',
            data: {
                refresh: 1
            },
            success: function (data) {
                show_alert(data.message || 'Refreshed All Workers', 'success');
            },
            error: function (data) {
                show_alert(data.responseText, "danger");
            }
        });
    });

    $('#worker-pool-restart').on('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        $('.dropdown-toggle').dropdown('hide');

        var workername = $('#workername').text();

        $.ajax({
            type: 'POST',
            url: url_prefix() + '/api/worker/pool/restart/' + workername,
            dataType: 'json',
            data: {
                workername: workername
            },
            success: function (data) {
                show_alert(data.message, "success");
            },
            error: function (data) {
                show_alert(data.responseText, "danger");
            }
        });
    });

    $('#worker-shutdown').on('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        $('.dropdown-toggle').dropdown('hide');

        var workername = $('#workername').text();

        $.ajax({
            type: 'POST',
            url: url_prefix() + '/api/worker/shutdown/' + workername,
            dataType: 'json',
            data: {
                workername: workername
            },
            success: function (data) {
                show_alert(data.message, "success");
            },
            error: function (data) {
                show_alert(data.responseText, "danger");
            }
        });
    });

    $('#worker-pool-grow').on('click', function (event) {
        event.preventDefault();
        event.stopPropagation();

        var workername = $('#workername').text(),
            grow_size = $('#pool-size').val();

        $.ajax({
            type: 'POST',
            url: url_prefix() + '/api/worker/pool/grow/' + workername,
            dataType: 'json',
            data: {
                'workername': workername,
                'n': grow_size,
            },
            success: function (data) {
                show_alert(data.message, "success");
            },
            error: function (data) {
                show_alert(data.responseText, "danger");
            }
        });
    });

    $('#worker-pool-shrink').on('click', function (event) {
        event.preventDefault();
        event.stopPropagation();

        var workername = $('#workername').text(),
            shrink_size = $('#pool-size').val();

        $.ajax({
            type: 'POST',
            url: url_prefix() + '/api/worker/pool/shrink/' + workername,
            dataType: 'json',
            data: {
                'workername': workername,
                'n': shrink_size,
            },
            success: function (data) {
                show_alert(data.message, "success");
            },
            error: function (data) {
                show_alert(data.responseText, "danger");
            }
        });
    });

    $('#worker-pool-autoscale').on('click', function (event) {
        event.preventDefault();
        event.stopPropagation();

        var workername = $('#workername').text(),
            min = $('#min-autoscale').val(),
            max = $('#max-autoscale').val();

        $.ajax({
            type: 'POST',
            url: url_prefix() + '/api/worker/pool/autoscale/' + workername,
            dataType: 'json',
            data: {
                'workername': workername,
                'min': min,
                'max': max,
            },
            success: function (data) {
                show_alert(data.message, "success");
            },
            error: function (data) {
                show_alert(data.responseText, "danger");
            }
        });
    });

    $('#worker-add-consumer').on('click', function (event) {
        event.preventDefault();
        event.stopPropagation();

        var workername = $('#workername').text(),
            queue = $('#add-consumer-name').val();

        $.ajax({
            type: 'POST',
            url: url_prefix() + '/api/worker/queue/add-consumer/' + workername,
            dataType: 'json',
            data: {
                'workername': workername,
                'queue': queue,
            },
            success: function (data) {
                show_alert(data.message, "success");
            },
            error: function (data) {
                show_alert(data.responseText, "danger");
            }
        });
    });

    $('#worker-queues').on('click', function (event) {
        event.preventDefault();
        event.stopPropagation();

        if (!event.target.id.startsWith("worker-cancel-consumer")) {
            return;
        }

        var workername = $('#workername').text(),
            queue = $(event.target).closest("tr").children("td:eq(0)").text();

        $.ajax({
            type: 'POST',
            url: url_prefix() + '/flowers/workers/cancel-consumer/' + workername + "/queue/" + queue,
            dataType: 'json',
            data: {
                'worker_name': workername,
                'queue': queue,
            },
            success: function (data) {
                showNotification(data.message);
            },
            error: function (data) {
                showErrorNotification(data.message);
            }
        });
    });

    $('#limits-table').on('click', function (event) {
        if (event.target.id.startsWith("task-timeout-")) {
            var timeout = parseInt($(event.target).siblings().closest("input").val()),
                type = $(event.target).text().toLowerCase(),
                taskname = $(event.target).closest("tr").children("td:eq(0)").text(),
                post_data = {'workername': $('#workername').text()};

            taskname = taskname.split(' ')[0]; // removes [rate_limit=xxx]
            post_data[type] = timeout;

            if (!Number.isInteger(timeout)) {
                show_alert("Invalid timeout value", "danger");
                return;
            }

            $.ajax({
                type: 'POST',
                url: url_prefix() + '/api/task/timeout/' + taskname,
                dataType: 'json',
                data: post_data,
                success: function (data) {
                    show_alert(data.message, "success");
                },
                error: function (data) {
                    show_alert($(data.responseText).text(), "danger");
                }
            });
        } else if (event.target.id.startsWith("task-rate-limit-")) {
            var taskname = $(event.target).closest("tr").children("td:eq(0)").text(),
                workername = $('#workername').text(),
                ratelimit = parseInt($(event.target).prev().val());

            taskname = taskname.split(' ')[0]; // removes [rate_limit=xxx]

            $.ajax({
                type: 'POST',
                url: url_prefix() + '/api/task/rate-limit/' + taskname,
                dataType: 'json',
                data: {
                    'workername': workername,
                    'ratelimit': ratelimit,
                },
                success: function (data) {
                    show_alert(data.message, "success");
                },
                error: function (data) {
                    show_alert(data.responseText, "danger");
                }
            });
        }
    });

    $('#task-revoke').on('click', function (event) {
        event.preventDefault();
        event.stopPropagation();

        var taskid = $('#taskid').text();

        $.ajax({
            type: 'POST',
            url: url_prefix() + '/api/task/revoke/' + taskid,
            dataType: 'json',
            data: {
                'terminate': false,
            },
            success: function (data) {
                show_alert(data.message, "success");
                document.getElementById("task-revoke").disabled = true;
                setTimeout(function () {
                    location.reload();
                }, 5000);
            },
            error: function (data) {
                show_alert(data.responseText, "danger");
            }
        });
    });

    $('#task-terminate').on('click', function (event) {
        event.preventDefault();
        event.stopPropagation();

        var taskid = $('#taskid').text();

        $.ajax({
            type: 'POST',
            url: url_prefix() + '/api/task/revoke/' + taskid,
            dataType: 'json',
            data: {
                'terminate': true,
            },
            success: function (data) {
                show_alert(data.message, "success");
                document.getElementById("task-terminate").disabled = true;
                setTimeout(function () {
                    location.reload();
                }, 5000);
            },
            error: function (data) {
                show_alert(data.responseText, "danger");
            }
        });
    });

    function sum(a, b) {
        return parseInt(a, 10) + parseInt(b, 10);
    }

    function format_time(timestamp) {
        var time = $('#time').val(),
            prefix = time && time.startsWith('natural-time') ? 'natural-time' : 'time';

        // If 'natural-time', return a human-readable relative time in the local timezone
        if (prefix === 'natural-time') {
            return moment.unix(timestamp).local().fromNow(); // Convert to local time and show relative format
        }

        // Otherwise, return the formatted date/time in local time ('YYYY-MM-DD HH:mm:ss.SSS')
        return moment.unix(timestamp).local().format('YYYY-MM-DD HH:mm:ss.SSS');
    }

    function isColumnVisible(name) {
        var columns = $('#columns').val();
        if (columns === "all")
            return true;
        if (columns) {
            columns = columns.split(',').map(function (e) {
                return e.trim();
            });
            return columns.indexOf(name) !== -1;
        }
        return true;
    }

    $.urlParam = function (name) {
        var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(window.location.href);
        return (results && results[1]) || 0;
    };

    $(document).ready(function () {
        //https://github.com/twitter/bootstrap/issues/1768
        var shiftWindow = function () {
            scrollBy(0, -50);
        };
        if (location.hash) {
            shiftWindow();
        }
        window.addEventListener("hashchange", shiftWindow);

        // Make bootstrap tabs persistent
        $(document).ready(function () {
            if (location.hash !== '') {
                $('a[href="' + location.hash + '"]').tab('show');
            }

            // Listen for tab shown events and update the URL hash fragment accordingly
            $('.nav-tabs a[data-bs-toggle="tab"]').on('shown.bs.tab', function (event) {
                const tabPaneId = $(event.target).attr('href').substr(1);
                if (tabPaneId) {
                    window.location.hash = tabPaneId;
                }
            });
        });
    });

    $(document).ready(function () {
        if (!active_page('/') && !active_page('/flowers/workers')) {
            return;
        }

        $.ajax({
            url: url_prefix() + '/flowers/workers?json=1',
            type: "GET",
            dataType: "json",
            success: function (data) {
                updateFlowerTableData(data);
            },
            error: function (error) {
                console.error("Error fetching flower workers data: ", error);
                showErrorNotification("Error fetching flower workers data");
            },
        })

        if (flower_worker_auto_refresh) {
            runFlowerTableDataUpdate();
        }

    });

    function runFlowerTableDataUpdate() {
        flower_worker_auto_refresh_interval = setInterval(function () {
            $.ajax({
                url: url_prefix() + '/flowers/workers?json=1',
                type: "GET",
                dataType: "json",
                success: function (data) {
                    updateFlowerTableData(data);
                },
                error: function (error) {
                    console.error("Error fetching flower workers data: ", error);
                    showErrorNotification("Error fetching flower workers data");
                },
            })
        }, 1 * 5000);
    }

    window.runFlowerTableDataUpdate = runFlowerTableDataUpdate;

    function updateFlowerTableData(data) {
        var tableBody = $("#flower-workers-table");

        tableBody.empty();
        if (data.data.length === 0) {
            var row = $("<div class='table-row'>");
            row.append($("<div style=\"width: 100%; text-align: center\">Немає активник воркерів</div></div>"));
            tableBody.append(row);
        }

        $.each(data.data, function (index, worker) {
            var row = $("<div class=\"table-row\">");
            row.append($("<div style=\"width: 13%\">")
                .html(`<a href="${url_prefix()}/flowers/worker/${encodeURIComponent(worker.hostname)}">${worker.hostname} + '</a>`));
            row.append($("<div style=\"width: 13%\">").text(worker.status));
            row.append($("<div style=\"width: 13%\">").text(worker.active));
            row.append($("<div style=\"width: 13%\">").text(worker["task-received"] ? worker["task-received"] : 0));
            row.append($("<div style=\"width: 13%\">").text(worker["task-failed"] ? worker["task-failed"] : 0));
            row.append($("<div style=\"width: 12%\">").text(worker["task-succeeded"] ? worker["task-succeeded"] : 0));
            row.append($("<div style=\"width: 12%\">").text(worker["task-retried"] ? worker["task-retried"] : 0));

            var queuesCell = $("<div style=\"width: 11%\">");
            $.each(worker["loadavg"], function (queueIndex, queue) {
                queuesCell.append(queue);
                if (queueIndex < worker["loadavg"].length - 1) {
                    queuesCell.append(", ");
                }
            });
            row.append(queuesCell);

            tableBody.append(row);
        });
    }

    let page = 1;

    window.onload = function () {
        updatePageNumber();
    };

    window["nextTaskPage"] = function nextPage() {
        page += 1;
        updatePageNumber();
        updateTasksData();
    }

    window["previousTaskPage"] = function previousPage() {
        if (page > 1) {
            page -= 1;
            updatePageNumber();
            updateTasksData();
        }
    }

    window["filterFlowerTasks"] = function filterFlowerTasks() {
        event.preventDefault();
        updateTasksData();
    }

    window["resetTaskForm"] = function resetTaskForm() {
        event.preventDefault();
        $("#state-filter").val("all");
        $("#search-name-filter").val("");
        updateTasksData();
    }

    function updateTasksData() {
        let selectedState = $("#state-filter").val();
        let selectedSearchValue = $("#search-name-filter").val();

        $.ajax({
            url: url_prefix() + `/flowers/tasks/datatable?limit=10&page=${page}&state=${selectedState}&search=${selectedSearchValue}`,
            type: "GET",
            dataType: "json",
            success: function (data) {
                var tableBody = $("#flower-tasks-table");
                tableBody.empty();
                if (data.data.length === 0) {
                    var row = $("<div class='table-row'>");
                    row.append($("<div style=\"width: 100%; text-align: center\">Немає активник задач</div></div>"));
                    tableBody.append(row);
                }
                $.each(data.data, function (index, task) {
                    var row = $("<div class=\"table-row\">");
                    row.append($("<div style=\"width: 6%\">").text(task.name));
                    row.append($("<div style=\"width: 18%\">").html(`<a href="${url_prefix()}/flowers/task/${encodeURIComponent(task.uuid)}">${task.uuid}</a>`));
                    switch (task.state) {
                        case 'SUCCESS':
                            row.append($("<div style=\"width: 7%\">").html('<span class="badge bg-success">' + task.state + '</span>'));
                            break;
                        case 'FAILURE':
                            row.append($("<div style=\"width: 7%\">").html('<span class="badge bg-danger">' + task.state + '</span>'));
                            break;
                        default:
                            row.append($("<div style=\"width: 7%\">").html('<span class="badge bg-secondary">' + task.state + '</span>'));
                    }
                    row.append($("<div style=\"width: 9%\">").text(task.args));
                    row.append($("<div style=\"width: 9%\">").text(task.kwargs));
                    row.append($("<div style=\"width: 8%\">").text(task.result));
                    row.append($("<div style=\"width: 12%\">").text(format_time(task.received)));
                    row.append($("<div style=\"width: 12%\">").text(format_time(task.started)));
                    row.append($("<div style=\"width: 9%\">").text(task.runtime ? task.runtime.toFixed(2) : task.runtime));
                    row.append($("<div style=\"width: 9%\">").html(`<a href="${url_prefix()}/flowers/worker/${encodeURIComponent(task.worker)}">${task.worker}</a>`));

                    tableBody.append(row);

                    renderPagination(data.page, data.total_pages, data.start_page, data.end_page);
                });
            },
            error: function (error) {
                console.error("Error fetching flower tasks data: ", error);
                showErrorNotification("Error fetching flower tasks data");
            },
        })
    }

    function renderPagination(currentPage, totalPages, startPage, endPage) {
        const wrapper = $("#pagination-wrapper");
        wrapper.empty();

        if (currentPage > 1) {
            wrapper.append(`
      <li class="pagination-wrapper-option" onclick="window.goToPage(${currentPage - 1})">
        <div class="pagination-wrapper-option-button" aria-label="Previous page">
          <svg height="20px" viewBox="0 0 27 24"><path d="M15.1667 8L11 12.1667L15.1667 16.3333" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
      </li>
    `);
        }

        if (currentPage > 3) {
            wrapper.append(`
      <li class="pagination-wrapper-option" onclick="window.goToPage(1)">
        <div class="pagination-wrapper-option-button">1</div>
      </li>
      <li class="ml-20"><span class="pagination-ellipsis">&hellip;</span></li>
    `);
        }

        for (let p = startPage; p <= endPage; p++) {
            wrapper.append(`
      <li class="pagination-wrapper-option ml-20">
        <div class="pagination-wrapper-option-button ${p === currentPage ? 'pagination-wrapper-option-button-active' : ''}"
             onclick="window.goToPage(${p})">${p}</div>
      </li>
    `);
        }

        if (currentPage < totalPages - 2) {
            wrapper.append(`
      <li class="ml-20"><span class="pagination-ellipsis">&hellip;</span></li>
      <li class="pagination-wrapper-option ml-20" onclick="window.goToPage(${totalPages})">
        <div class="pagination-wrapper-option-button">${totalPages}</div>
      </li>
    `);
        }

        if (currentPage < totalPages) {
            wrapper.append(`
      <li class="pagination-wrapper-option ml-20" onclick="window.goToPage(${currentPage + 1})">
        <div class="pagination-wrapper-option-button" aria-label="Next page">
          <svg height="20px" viewBox="0 0 27 24"><path d="M11.2333 16L15.4 11.8333L11.2333 7.66667" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
      </li>
    `);
        }
    }

    window.goToPage = function(p) {
      page = p;
      updateTasksData();
    }


    function updatePageNumber() {
        if (document.getElementById("page-number") !== null) {
            document.getElementById("page-number").textContent = page;
        }
    }

    $(document).ready(function () {
        if (!active_page('/flowers/tasks')) {
            return;
        }

        updateTasksData();
    });

}(jQuery));
