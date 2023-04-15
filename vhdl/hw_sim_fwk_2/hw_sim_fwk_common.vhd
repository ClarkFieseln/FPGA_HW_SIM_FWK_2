library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all; 


-- Note: the followig metacomment is not part of the VHDL synthesis standard (IEEE P1076.6) so behavior is tool dependent.
-- synthesis translate_off
-- ######################
-- NOTE: add this module to hw_sim_fwk library in your project, and associate it only with Simulation.


package hw_sim_fwk_common is  
  function slv_to_string ( slv_value : std_logic_vector) return string;
  function binary_to_character(value : in std_logic) return character;
  function std_logic_to_character(value : in std_logic) return character;
  function character_to_bit(value : in character) return bit;
  function character_to_std_logic(value : in character) return std_logic;
end hw_sim_fwk_common;

package body hw_sim_fwk_common is
    function slv_to_string ( slv_value: std_logic_vector) return string is
        variable str_temp : string (slv_value'length downto 1) := (others => NUL);
    begin
        for i in slv_value'length downto 1 loop
            str_temp(i) := std_logic'image(slv_value((i-1)))(2);
        end loop;
        return str_temp;
    end function;

    function binary_to_character(value : in std_logic) return character is
    begin
        return character'val(to_integer(unsigned'('0' & value)));
    end function binary_to_character;
    
    function std_logic_to_character(value : in std_logic) return character is
      variable ret_val : character;
    begin
        case value is
            -- uninitialized
            when 'U' =>
                ret_val := 'U';
            -- unknown
            when 'X' =>
                ret_val := 'X';
            -- logic 0
            when '0' =>
                ret_val := '0';
            -- logic 1
            when '1' =>
                ret_val := '1';
            -- high impedance
            when 'Z' =>
                ret_val := 'Z';
            -- weak signal, can't tell if it should be 0 or 1
            when 'W' =>
                ret_val := 'W';
            -- weak signal that should probably go to 0
            when 'L' =>
                ret_val := 'L';
            -- weak signal that should probably go to 1
            when 'H' =>
                ret_val := 'H';
            -- other values set to unknown
            when others =>
                ret_val := 'X';
        end case;
        return ret_val;
    end function std_logic_to_character;

    function character_to_bit(value : in character) return bit is
        variable ret_val : bit := '0';
    begin        
        if value = '1' then
            ret_val := '1';
        end if;
        return ret_val;
    end function character_to_bit;

    function character_to_std_logic(value : in character) return std_logic is
      variable ret_val : std_logic;
    begin
        case value is
            -- uninitialized
            when 'U' =>
                ret_val := 'U';
            -- unknown
            when 'X' =>
                ret_val := 'X';
            -- logic 0
            when '0' =>
                ret_val := '0';
            -- logic 1
            when '1' =>
                ret_val := '1';
            -- high impedance
            when 'Z' =>
                ret_val := 'Z';
            -- weak signal, can't tell if it should be 0 or 1
            when 'W' =>
                ret_val := 'W';
            -- weak signal that should probably go to 0
            when 'L' =>
                ret_val := 'L';
            -- weak signal that should probably go to 1
            when 'H' =>
                ret_val := 'H';
            -- other values set to unknown
            when others =>
                ret_val := 'X';
        end case;
        return ret_val;
    end function character_to_std_logic;    
end hw_sim_fwk_common;

-- synthesis translate_on
-- ######################
