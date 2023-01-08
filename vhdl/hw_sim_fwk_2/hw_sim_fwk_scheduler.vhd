library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;
library hw_sim_fwk;
use hw_sim_fwk.hw_sim_fwk_common.all;


-- Note: the followig metacomment is not part of the VHDL synthesis standard (IEEE P1076.6) so behavior is tool dependent.
-- synthesis translate_off
-- ######################
-- NOTE: add this module to hw_sim_fwk library in your project, and associate it only with Simulation.


entity hw_sim_fwk_scheduler is
    generic(
        FIFO_PATH                 : string  := "\\.\pipe\";
        STIMULUS_FILE_NAME        : string  := FIFO_PATH & "fifo_app_to_sim";
        OUTPUT_FILE_NAME          : string  := FIFO_PATH & "fifo_sim_to_app";
        CLOCK_PERIOD              : time    := 20 ns;
        NR_BUTTONS                : integer := 6;
        NR_SWITCHES               : integer := 6;
        NR_DIS                    : integer := 10;
        NR_DOS                    : integer := 10;
        NR_LEDS                   : integer := 12
    );
    port(
        hw_clock  : out std_logic_vector(0 downto 0);
        hw_reset  : out std_logic_vector(0 downto 0);
        hw_button : out std_logic_vector(NR_BUTTONS - 1 downto 0);
        hw_switch : out std_logic_vector(NR_SWITCHES - 1 downto 0);
        hw_di     : out std_logic_vector(NR_DIS - 1 downto 0);
        hw_do     : in std_logic_vector(NR_DOS - 1 downto 0);
        hw_led    : in std_logic_vector(NR_LEDS - 1 downto 0)
    );
    -- signals
    constant NR_INPUT_SIGNALS    : integer := 5;    
    constant NR_OUTPUT_SIGNALS   : integer := 2;
    constant MAX_IN_VECTOR_SIZE  : integer := maximum((NR_BUTTONS,NR_SWITCHES,NR_DIS));
    constant MAX_OUT_MSG_SIZE    : integer := NR_DOS + NR_LEDS + 6; -- +6 to cover 2 times index, separator, comma
    constant LED_MSG_SIZE        : integer := NR_LEDS + 3; -- +3 to account for index, separator, comma
    constant DO_MSG_SIZE         : integer := NR_DOS + 3; -- +3 to account for index, separator, comma
    constant hw_clock_index      : integer := 0;
    constant hw_reset_index      : integer := 1;
    constant hw_button_index     : integer := 2;
    constant hw_switch_index     : integer := 3;
    constant hw_di_index         : integer := 4;
    constant hw_do_index         : integer := 0;
    constant hw_led_index        : integer := 1;
    type INPUT_SIGNAL_ARRAY is array (0 to NR_INPUT_SIGNALS-1) of std_logic_vector;
    type INPUT_SIGNAL_LEN_ARRAY is array (0 to NR_INPUT_SIGNALS-1) of integer;  
    signal input_signal          : INPUT_SIGNAL_ARRAY(open)(MAX_IN_VECTOR_SIZE-1 downto 0) := (others => (others => '0'));
    constant input_signal_len    : INPUT_SIGNAL_LEN_ARRAY := (1,1,NR_BUTTONS,NR_SWITCHES,NR_DIS);  
    type OUTPUT_SIGNAL_ARRAY is array (0 to NR_OUTPUT_SIGNALS-1) of std_logic_vector;
    type OUTPUT_SIGNAL_LEN_ARRAY is array (0 to NR_OUTPUT_SIGNALS-1) of integer;  
    shared variable out_msg      : string(MAX_OUT_MSG_SIZE downto 1);
    shared variable out_len      : integer := 0;
    signal hw_led_prev           : std_logic_vector(NR_LEDS - 1 downto 0);
    signal hw_do_prev            : std_logic_vector(NR_DOS - 1 downto 0);
end hw_sim_fwk_scheduler;

architecture arch of hw_sim_fwk_scheduler is
begin
    -- cable through
    hw_clock(input_signal_len(hw_clock_index)-1 downto 0) <= input_signal(hw_clock_index)(input_signal_len(hw_clock_index)-1 downto 0);
    hw_reset(input_signal_len(hw_reset_index)-1 downto 0) <= input_signal(hw_reset_index)(input_signal_len(hw_reset_index)-1 downto 0);
    hw_button(input_signal_len(hw_button_index)-1 downto 0) <= input_signal(hw_button_index)(input_signal_len(hw_button_index)-1 downto 0);
    hw_switch(input_signal_len(hw_switch_index)-1 downto 0) <= input_signal(hw_switch_index)(input_signal_len(hw_switch_index)-1 downto 0);
    hw_di(input_signal_len(hw_di_index)-1 downto 0) <= input_signal(hw_di_index)(input_signal_len(hw_di_index)-1 downto 0);
    
    -- simulation proc_led_out
    -- #######################
    proc_led_out : process(hw_led)
    begin
        if hw_led /= hw_led_prev then
            out_msg((LED_MSG_SIZE + out_len) downto (out_len + 1)) := to_string(hw_led_index) & ":" & to_string(hw_led) & ",";
            out_len := out_len + LED_MSG_SIZE;
            hw_led_prev <= hw_led;
        end if;
    end process proc_led_out;
    
    -- simulation proc_do_out
    -- ######################
    proc_do_out : process(hw_do)
    begin
        if hw_do /= hw_do_prev then
            out_msg((DO_MSG_SIZE + out_len) downto (out_len + 1)) := to_string(hw_do_index) & ":" & to_string(hw_do) & ",";
            out_len := out_len + DO_MSG_SIZE;
            hw_do_prev <= hw_do;
        end if;
    end process proc_do_out;
    
    -- scheduler
    -- connected to external simulator via FIFOs (named pipes)
    -- #######################################################
    proc_scheduler : process        
        file     i_file          : text;
        file     o_file          : text;
        variable i_line          : line;   
        variable index           : integer;
        variable separator       : character;
        variable stimulus_string : string(MAX_IN_VECTOR_SIZE downto 1);
        variable last_comma      : character; 
        variable clock_in_str    : string(1 downto 1);
        variable open_status     : file_open_status;        
        variable initialized     : boolean := false;
    begin
        -- initialization?
        -- ###############
        if initialized = false then
            initialized := true;          
            -- open stimulus FIFO (named-pipe) created in external simulation app - VHDL is NOT able to create named pipes!
            loop
                file_open(open_status, i_file, STIMULUS_FILE_NAME,  read_mode);
                exit when open_status = open_ok;
            end loop;            
            -- open output file, which is a FIFO (named pipe), is created by the external application.    
            loop
                file_open(open_status, o_file, OUTPUT_FILE_NAME,  write_mode);                
                exit when open_status = open_ok;
            end loop;
            -- read stimulus data
            ---------------------
            readline(i_file, i_line);        
            -- write output data
            --------------------
            if out_len > 0 then
                write(o_file, out_msg(out_len downto 1));
                out_len := 0;
            else
                write(o_file, "*");
            end if;
            flush(o_file);                           
            -- process stimulus data
            ------------------------           
            while i_line'length /= 0 loop                
                read(i_line, index);
                if index < NR_INPUT_SIGNALS then
                    read(i_line, separator);                      
                    read(i_line, stimulus_string(input_signal_len(index) downto 1));
                    read(i_line, last_comma);     
                    -- process input signal                               
                    for i in 0 to input_signal_len(index)-1 loop                                                       
                        input_signal(index)(i) <= character_to_std_logic(stimulus_string(i+1));
                    end loop;                 
                    -- async reset?                    
                    if (index = hw_reset_index) and (stimulus_string(1) = '1') then
                        input_signal(hw_button_index) <= (others => '0');  
                        input_signal(hw_switch_index) <= (others => '0');    
                        input_signal(hw_di_index) <= (others => '0');
                    -- clock?                  
                    -- set flag to further process external clock signal after receiving all signals?
                    elsif index = hw_clock_index then                  
                        clock_in_str(1) := stimulus_string(1);
                    end if;
                end if;
            end loop;
            -- further process external clock signal?
            if (clock_in_str(1) = '1') or (clock_in_str(1) = '0') then                                      
                wait for CLOCK_PERIOD / 2;
                clock_in_str(1) := 'X';
            end if;
        -- check external signals
        -- ######################
        else
            -- with this loop we avoid re-checking the variable "initialized" every time      
            loop
                -- read stimulus data
                ---------------------
                readline(i_file, i_line);                 
                -- write output data
                --------------------
                if out_len > 0 then
                    write(o_file, out_msg(out_len downto 1));
                    out_len := 0;
                else
                    write(o_file, "*");
                end if;
                flush(o_file); 
                -- process stimulus data
                ------------------------
                while i_line'length /= 0 loop                    
                    read(i_line, index);
                    if index < NR_INPUT_SIGNALS then
                        read(i_line, separator);                           
                        read(i_line, stimulus_string(input_signal_len(index) downto 1));
                        read(i_line, last_comma);
                        -- process signal                       
                        for i in 0 to input_signal_len(index)-1 loop                                                             
                            input_signal(index)(i) <= character_to_std_logic(stimulus_string(i+1));
                        end loop;                       
                        -- async reset?
                        if index = hw_reset_index and stimulus_string(1) = '1' then
                            input_signal(hw_button_index) <= (others => '0');  
                            input_signal(hw_switch_index) <= (others => '0');    
                            input_signal(hw_di_index) <= (others => '0');
                        -- clock?                     
                        -- set flag to further process external clock signal after receiving all signals?
                        elsif index = hw_clock_index then
                            clock_in_str(1) := stimulus_string(1);
                        end if;
                    end if;
                end loop;
                -- further process external clock signal?
                if (clock_in_str(1) = '1') or (clock_in_str(1) = '0') then                                      
                    wait for CLOCK_PERIOD / 2;
                    clock_in_str(1) := 'X';
                end if;
            end loop;
        end if;
    end process proc_scheduler;
end arch;

-- synthesis translate_on
-- ######################
