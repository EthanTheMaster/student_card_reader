var ws = new WebSocket("wss://127.0.0.1:8765/");

var accepting_card_input = false;

ws.onmessage = function (event) {
    var last_name_field = document.getElementById("kiosk-last-name-field");
    var id_field = document.getElementById("kiosk-student-id-field");
    
    student = JSON.parse(event.data);
    name_split = student.name.split(" ");

    id_field.setAttribute("type", "text");

    // Fill in fields through React
    var native_input_value_setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
    var event = new Event('input', { bubbles: true });
    native_input_value_setter.call(last_name_field, student.name.split(" ").pop());
    last_name_field.dispatchEvent(event);
    native_input_value_setter.call(id_field, student.id);
    id_field.dispatchEvent(event);

    accepting_card_input = false;
};

ws.onopen = function (event) {
    setInterval(function () {
        var last_name_field = document.getElementById("kiosk-last-name-field");
        var id_field = document.getElementById("kiosk-student-id-field");
        if (
            id_field != null &&
            last_name_field.value == "" &&
            id_field.value == "" &&
            !accepting_card_input
        ) {
            accepting_card_input = true
            ws.send("Ready");
        }
    }, 500);
};

