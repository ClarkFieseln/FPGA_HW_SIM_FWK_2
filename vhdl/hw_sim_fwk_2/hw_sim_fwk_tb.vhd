library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;
use work.top_module;
library hw_sim_fwk;
use hw_sim_fwk.all;
entity hw_sim_fwk_tb is
end hw_sim_fwk_tb;


architecture arch of hw_sim_fwk_tb is
    -- constants for generic map:
    -- ##########################
    -- hw_sim_fwk_tb
    constant SIMULATE_BUTTON_IN_TESTBENCH : boolean := false; -- otherwise button simulated externally 
    constant CLOCK_PERIOD                 : time    := 20 ns;
    -- modMCounter
    constant M                            : integer := 10;
    constant N                            : integer := 4;
    constant T                            : time    := CLOCK_PERIOD;
    -- hw_sim_fwk_scheduler   
    constant FIFO_PATH                    : string  := "\\.\pipe\";  
    constant STIMULUS_FILE_NAME           : string  := FIFO_PATH & "fifo_app_to_sim";
    constant OUTPUT_FILE_NAME             : string  := FIFO_PATH & "fifo_sim_to_app";
    constant NR_DIS                       : integer := 10;    
    constant NR_SWITCHES                  : integer := 6;    
    constant NR_BUTTONS                   : integer := 6;    
    constant NR_LEDS                      : integer := 12;    
    constant NR_DOS                       : integer := 10;
    -- signals:
    -- common signals
    -- ##############
    signal hw_clock_tb                    : std_logic; -- input common for all modules
    signal reset_tb                       : std_logic; -- input common for all modules
    -- ########
    -- modMCounter
    -- ###########
    -- Outputs
    signal complete_tick_tb               : std_logic;
    signal count_tb                       : std_logic_vector(N - 1 downto 0);
    -- dio
    -- ###
    --Inputs
    signal di_tb                          : std_logic_vector(NR_DIS - 1 downto 0);
    --Outputs
    signal do_tb                          : std_logic_vector(NR_DOS - 1 downto 0);
    -- switch leds
    -- ###########
    --Inputs
    signal switch_tb                      : std_logic_vector(NR_SWITCHES - 1 downto 0);
    signal button_tb                      : std_logic_vector(NR_BUTTONS - 1 downto 0);
    -- Note:
    -- button_tb_dummy is used when the button is simulated in the testbench, (see option in port map further below)
    -- the signals triggered by the external simulator go to nirvana in that case..
    signal button_tb_dummy                : std_logic_vector(NR_BUTTONS - 1 downto 0);
    --Outputs
    signal led_tb                         : std_logic_vector(NR_LEDS - 1 downto 0);  
begin
    -- asserts
    assert ((NR_BUTTONS = NR_SWITCHES)) report ("Unequal nr. of switches and buttons = " & integer'image(NR_SWITCHES) & ", " & integer'image(NR_BUTTONS)) severity failure;
    assert ((NR_LEDS = NR_SWITCHES*2)) report ("Nr. of LEDS not double nr. of buttons = " & integer'image(NR_LEDS) & ", " & integer'image(NR_BUTTONS)) severity failure;   
  
    -- instantiate top_module
    -- ######################
    top_module_unit : entity top_module
        generic map(
            -- modMCounter
            M           => M,
            N           => N,
            -- switch_leds
            NR_SWITCHES => NR_SWITCHES,
            NR_BUTTONS  => NR_BUTTONS,
            NR_LEDS     => NR_LEDS,
            -- dio
            NR_DIS      => NR_DIS,
            NR_DOS      => NR_DOS
        )
        port map(
            -- common
            reset_in          => reset_tb,
            clock_in          => hw_clock_tb,
            -- modMCounter
            complete_tick_out => complete_tick_tb,
            count_out         => count_tb,
            -- switch_leds
            switch_in         => switch_tb,
            button_in         => button_tb,
            led_out           => led_tb,
            -- dio
            di_in             => di_tb,
            do_out            => do_tb
        );        
 
    -- instantiate hw scheduler, connected to external scheduler
    -- #########################################################
    hw_sim_fwk_scheduler_unit : entity hw_sim_fwk_scheduler
        generic map(
            FIFO_PATH                 => FIFO_PATH,
            STIMULUS_FILE_NAME        => STIMULUS_FILE_NAME,
            OUTPUT_FILE_NAME          => OUTPUT_FILE_NAME,
            CLOCK_PERIOD              => CLOCK_PERIOD,
            NR_BUTTONS                => NR_BUTTONS,
            NR_SWITCHES               => NR_SWITCHES,
            NR_DIS                    => NR_DIS,
            NR_DOS                    => NR_DOS,
            NR_LEDS                   => NR_LEDS
        )
        port map(
            hw_clock(0) => hw_clock_tb,
            hw_reset(0) => reset_tb,
            hw_button   => button_tb,
            hw_switch   => switch_tb,
            hw_di       => di_tb,
            hw_do       => do_tb,
            hw_led      => led_tb
        );     
                  
    -- PROCESSES 
    -- #########
    -- active test-bench tests, parallel to external simulation
    -- when button_tb_dummy is used, then button_tb is set in this process
    -- instead of being triggered by the external simulator.
    -- ###################################################################
    g_conditional_tb_button_simulation_3oo3 : if SIMULATE_BUTTON_IN_TESTBENCH = true generate
        proc_testbench_main : process(hw_clock_tb, reset_tb)
            variable clock_periods : integer := 0;
        begin
            if reset_tb = '1' then
                button_tb(0) <= '0';
            elsif rising_edge(hw_clock_tb) then
                clock_periods := clock_periods + 1;
                if clock_periods = 8 then -- Note: hardcoded value for test.
                    -- reset_tb <= '1';
                    button_tb(0)  <= not button_tb(0);
                    clock_periods := 0;
                end if;
            end if;
        end process proc_testbench_main;
    end generate g_conditional_tb_button_simulation_3oo3;
end arch;


