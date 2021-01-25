// Establish connection with host
const socket = io.connect('http://' + document.domain + ':' + location.port);

// Conversation box selector
const conversation_box = $('div.conversation-box');

socket.on('connect', function() {

    // Retrieving user's form input when they submit
    $('form').on('submit', function(e) {

        // Preventing submit default functionality
        e.preventDefault();

        const selector = $('input.text-msg');

        // Get user's text message
        let user_input = selector.val();

        // If message is not empty emit
        if(user_input) {
            socket.emit('message sent', { message: user_input });

            // Clear message field and focus
            selector.val('').focus();
          }
    });
});

// Scrolling to the bottom of message box as conversation flows
function scroll_to_bottom() {

    const chat_box = $('.conversation-box');
    const height = chat_box[0].scrollHeight;
    chat_box.scrollTop(height);

}

// Adding message to conversation box
function append_message(type, json) {

    conversation_box.append(

            '<div class="message ' + type + '">' +
                '<span>' + json.message + '</span>' +
                '<div class="message-timestamp">' + json.time_sent + '</div>' +
            '</div>'

    );

    scroll_to_bottom();

}

// Getting and displaying sent message
socket.on('display sent message', function(json) {

    append_message('sent', json);

});

// Getting and displaying received message
socket.on('display received message', function(json) {

    append_message('received', json);

});

// Getting and displaying chosen ticket
// Used structure and style inspiration from: https://codepen.io/Sillzen/pen/GqzmWj
socket.on('display ticket', function(json) {

    conversation_box.append(

            '<div class="train-ticket">' +
                '<div class="header">' + json.fareProvider + '</div>' +
                    '<ul>' +
                        '<li>' +
                            '<span>' + json.departureStationName + '</span>' +
                            '<span>></span>' +
                            '<span>' + json.arrivalStationName + '</span>' +
                        '</li>' +
                        '<li>' +
                            '<span data="Departure">' + json.departureTime + '</span>' +
                            '<span data="Arrival">' + json.arrivalTime + '</span>' +
                            '<span data="Duration">' + json.duration + '</span>' +
                            '<span data="Layover">' + json.changes + '</span>' +
                        '</li>' +
                        '<li>' +
                            '<span data="Departure Date">' + json.departDate + '</span>' +
                            '<span data="Ticket Price">£' + json.ticketPrice + '</span>' +
                        '</li>'

                        + (json.isReturn ? '' +
                        '<li>' +
                            '<span data="Return Date">' + json.returnDate + '</span>' +
                            '<span>' + json.returnTicketType + '</span>' +
                        '</li>' : '') + '' +
                    '</ul>' +
            '</div>'

    );

    scroll_to_bottom()

});
