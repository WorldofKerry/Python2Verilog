module get_data_tb (
);
    reg _clock;
    reg _start;
    reg _reset;
    reg _ready;
    reg signed [31:0] addr;
    wire _done;
    wire _valid;
    wire signed [31:0] _out0;
    get_data DUT (
        ._clock(_clock),
        ._start(_start),
        ._reset(_reset),
        ._ready(_ready),
        .addr(addr),
        ._done(_done),
        ._valid(_valid),
        ._out0(_out0)
        );
    always #5 _clock = !_clock;
    initial begin
        _clock = 0;
        _start = 0;
        _ready = 1;
        _reset = 1;
        @(negedge _clock);
        _reset = 0;
        // ============ Test Case 0 with arguments (264,) ============
        addr = $signed(264);
        _start = 1;
        @(negedge _clock);
        addr = 'x; // only need inputs when start is set
        _start = 0;
        while ((!(_done) || !(_ready))) begin
            @(posedge _clock);
            if (_ready) begin
                $display("%0d, %0d, %0d", _ready, _valid, _out0);
            end
            @(negedge _clock);
        end
        $finish;
    end
endmodule

/*
MIT License

Copyright (c) 2023 Kerry Wang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

module read32to8_tb (
);
    reg _clock;
    reg _start;
    reg _reset;
    reg _ready;
    reg signed [31:0] base;
    reg signed [31:0] count;
    wire _done;
    wire _valid;
    wire signed [31:0] _out0;
    read32to8 DUT (
        ._clock(_clock),
        ._start(_start),
        ._reset(_reset),
        ._ready(_ready),
        .base(base),
        .count(count),
        ._done(_done),
        ._valid(_valid),
        ._out0(_out0)
        );
    always #5 _clock = !_clock;
    initial begin
        _clock = 0;
        _start = 0;
        _ready = 1;
        _reset = 1;
        @(negedge _clock);
        _reset = 0;
        // ============ Test Case 0 with arguments (256, 2) ============
        base = $signed(256);
        count = $signed(2);
        _start = 1;
        @(negedge _clock);
        base = 'x; // only need inputs when start is set
        count = 'x; // only need inputs when start is set
        _start = 0;
        while ((!(_done) || !(_ready))) begin
            @(posedge _clock);
            if (_ready) begin
                $display("%0d, %0d, %0d", _ready, _valid, _out0);
            end
            @(negedge _clock);
        end
        $finish;
    end
endmodule

/*
MIT License

Copyright (c) 2023 Kerry Wang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/
